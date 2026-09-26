# 解析パイプライン

`engine.py` が1筆×1年の正式なルール実装です。`generate_demo.py` は公式2026年筆ポリゴンへ再現可能な模擬時系列を与え、Webアプリ用の静的成果を作ります。模擬値はUIとアルゴリズムの実演専用で、実在圃場の状態や精度を示しません。

## デモ成果の再生成

```powershell
$env:PYTHONPATH='pipeline'
.venv\Scripts\python.exe pipeline\generate_demo.py --fgb <南相馬市2026年筆ポリゴン.json>
.venv\Scripts\python.exe pipeline\validate_outputs.py
.venv\Scripts\python.exe -m pytest pipeline\tests -q
```

出力は `public/data/` の4ファイルです。判定閾値、観測数、雲マスク、小区画ルールは `config.json` に集約しています。

## 実観測への切替

### 認証不要の公開STAC経路（今回の配信データ）

Microsoft Planetary Computerの公開STACからSentinel-1 RTCとSentinel-2 L2Aを取得し、筆別CSVと静的成果を生成します。Earth Engine認証は不要です。

```powershell
$env:PYTHONPATH='pipeline'
.venv\Scripts\python.exe pipeline\extract_planetary_computer.py
.venv\Scripts\python.exe pipeline\build_from_gee_exports.py `
  --s1 tmp\planetary-computer\s1-vh.csv `
  --s2 tmp\planetary-computer\s2-ndvi.csv `
  --provenance tmp\planetary-computer\provenance.json
.venv\Scripts\python.exe pipeline\validate_outputs.py
```

この経路は、S2のCloud Probabilityバンドが公開STACにないため、SCL除外クラスと20 mバッファを使用します。Earth Engine経路と同じCloud Probability 40%未満を厳密に再現する必要がある場合は次の経路を使います。出典・シーンID・軌道・変換条件は`tmp/planetary-computer/provenance.json`に保存します。

### Earth Engine経路

1. Earth Engineを認証する。
2. 次を実行して、同一軌道のSentinel-1 VHと雲除去済みSentinel-2 NDVIをGoogle Driveへバッチ出力する。

```powershell
.venv\Scripts\python.exe pipeline\extract_earth_engine.py --project <GCP_PROJECT_ID>
```

3. エクスポートCSVを日付・圃場IDで結合し、`engine.classify_year` の観測スキーマへ渡す。
   次のコマンドで20%雲量を標準、必須窓不足時のみ30%までのフォールバックとして静的成果へ変換できます。

```powershell
$env:PYTHONPATH='pipeline'
.venv\Scripts\python.exe pipeline\build_from_gee_exports.py --s1 <S1_CSV> --s2 <S2_CSV>
```

4. `validate_outputs.py` と24筆・2名の独立目視検証を通す。

Earth Engineの認証情報やAPIキーはWebアプリへ含めません。シーン雲量20%を標準とし、不足窓だけ30%までの観測を採用する判断はエクスポート後に行います。
