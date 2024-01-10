#!/usr/bin/python3

from fastapi import FastAPI
from typing import List
import numpy as np
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from pydantic import BaseModel

app = FastAPI(
docs_url="/",
title="誤脱字無散",
description="""
## これはなにか

日本語テキストの誤字・脱字を検出するAPI群です。

入力されたテキストに対し、各文字が下記の表に示すどのエラーに最も近いかを判定して、
そのエラーコードの配列を作成します。

* 0	OK	誤字なし
* 1	deletion	1文字の抜け
* 2	insertion_a	余分な1文字の挿入
* 3	insertion_b	直前の文字列と一致する２文字以上の余分な文字の挿入
* 4	kanji-conversion_a	同一の読みを持つ漢字の入れ替え（誤変換）
* 5	kanji-conversion_b	近い読みを持つ漢字の入れ替え（誤変換）
* 6	substitution	1文字の入れ替え
* 7	transposition	隣接する２文字間の転置
* 8	others	その他の入力誤り

返り値はエンドポイントごとに異なります。

1. /errors エラーコードの配列をそのまま返します。
2. /aggregate 連続するエラーコードを集約して返します。
3. /markup 元の文字列のエラー箇所を強調して返します。

## Acknowledgement

このWebAPIは桐生佳介氏による誤字脱字検出モデル(recruit-jp/japanese-typo-detector-roberta-base)をAPI化したものです。
性能について、誤りの検出は50-70%程度、誤検出は10%程度と報告されています。また、次のような制約があるとされています。

* 複数の誤りを保つケースを十分学習できておらず、2つ目以降を見逃すことがある。
* 全角アルファベットの混入（例：私たちはｋこのモデルを公開）といった例を捕捉できない。

### ライセンス

recruit-jp/japanese-typo-detector-roberta-base のライセンスについて以下の通り言及されています。
* 本モデルは京都大学大学院情報学研究科知能情報学コース言語メディア研究室
 (https://nlp.ist.i.kyoto-u.ac.jp/ )が公開しているRoBERTaの事前学習モデル
(ku-nlp/roberta-base-japanese-char-wwm)をFine-Tuningしたものです。
* 本モデルは事前学習モデルのライセンス"CC-BY-SA 4.0"を継承します。

### 参照

* https://blog.recruit.co.jp/data/articles/typo-detector/
* https://huggingface.co/recruit-jp/japanese-typo-detector-roberta-base


""")

# モデルとトークナイザーの初期化
model_name = 'recruit-jp/japanese-typo-detector-roberta-base'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = model.to(device)


desc_aggregate_errors = '''
### 説明

入力に対し、連続するエラーコードを一つのまとまりとして返します。

例えば

{ "text": "これは日本語の誤植を検出する真相学習モデルです。" }

に対する応答は

[[0, 14, 0 ], [14, 2, 4], [16, 8, 0]]

となります。これは下記の意味になります。

* 0文字目から14文字 エラーなし
* 14文字目から2文字 誤変換
* 16文字目から8文字 エラーなし
'''

desc_list_errors = '''
### 説明

入力に対応するエラーをリストで返します。

{ "text": "これは日本語の誤植を検出する真相学習モデルです。" }

に対する応答は

[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0]

となります。
'''

desc_markup = '''
### 説明

入力に対応するエラー箇所をアスタリスクで強調表示します。

{ "text": "これは日本語の誤植を検出する真相学習モデルです。" }

に対する応答は

{ "text": "これは日本語の誤植を検出する\*真相\*学習モデルです。" }

となります。
'''

class TargetInput(BaseModel):
    text: str

class TextResponse(BaseModel):
    text: str

@app.post("/errors", summary="list erros for each characters", description=desc_list_errors)
async def plain(target: TargetInput) -> List[int]:
    error_type_inds = get_errortypes(target)
    return error_type_inds

@app.post("/markup", summary="mark up errors", description=desc_markup)
async def plain(target: TargetInput) -> TextResponse:
    error_type_inds = get_errortypes(target)
    aggregated = aggregate_errors(error_type_inds)

    content = ''

    for error in aggregated:

        str = target.text[error[0]: error[0]+error[1]]
        type = error[2]
        if ( type == 0 ):
            content += str
        else:
            content += "*" + str + "*"

    return TextResponse(text=content)


    
    
        


    return error_type_inds

@app.post("/aggregate", summary="aggregate same errors", description=desc_aggregate_errors)
async def aggregate(target: TargetInput) -> List[List[int]]:
    error_type_inds = get_errortypes(target)

    aggregated = aggregate_errors(error_type_inds)
    return aggregated


def get_errortypes(target: TargetInput) -> List[int]:
    # テキストをモデルに入力する形式に変換
    test_inputs = tokenizer(target.text, return_tensors='pt').input_ids
    test_outputs = model(test_inputs.to(device))

    # 各文字に対する誤植のインデックスを取得
    logits = test_outputs.logits.squeeze().tolist()[1:-1]
    error_type_inds = [np.argmax(logit) for logit in logits]
    return error_type_inds


def aggregate_errors(err_ind):
    if not err_ind:
        return []

    aggregated = []
    start_index = 0
    current_err_type = err_ind[0]
    length = 1

    for i in range(1, len(err_ind)):
        if err_ind[i] == current_err_type:
            length += 1
        else:
            aggregated.append([start_index, length, current_err_type])
            start_index = i
            current_err_type = err_ind[i]
            length = 1

    # Append the last segment
    aggregated.append([start_index, length, current_err_type])

    return aggregated
