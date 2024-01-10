# 概要

 https://blog.recruit.co.jp/data/articles/typo-detector/ で公開されている
 誤字脱字検出ツールをWebAPIとして使えるようにしたものです。

 多量のエクセルセルに対してチェックを掛けるため、マクロと組み合わせて利用することを想定しています。

## インストール・起動

```
uvicorn api:app
```
でローカルにWebサーバーが立ち上がります。APIの詳細は```http://localhost:8000```を見てください。

初回起動時にmodelのダウンロードが行われます。ダウンロード場所は既定でホームディレクトリになっていますが
`HF_HOME`の指定に従うようです。下記のコマンドで起動すると`HF_HOME=./`として動作します.

```
./run.sh
```

# 以下、APIの説明からのコピー

## これはなにか

日本語テキストの誤字・脱字を検出するAPIです。

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
