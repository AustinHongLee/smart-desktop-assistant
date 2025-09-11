# smart-desktop-assistant (MVP)

本機隱私優先的小助手（極簡版）：用 `memory_data.json` 做「稍微智慧」搜尋（模糊相似 + 關鍵詞重疊），並支援正/負回饋學習（排序越用越準）。

## 安裝
```bash
pip install -e .

使用
python -m assistant GL-05 預製圖 308
```

會列出 Top-N 結果，輸入編號即可開啟，並自動記錄學習偏置到 data/learn_bias.json。


---

## 驗收標準
- 能 `pip install -e .` 安裝。  
- 指令 `python -m assistant <關鍵詞>` 能顯示 Top-N。  
- 輸入編號可成功開啟該項（資料夾/檔案/URL）。  
- 執行過一次後，`data/learn_bias.json` 會生成，且再次查同樣關鍵詞時，排序有受到學習影響。  
- 所有檔案以 UTF-8 儲存，中文路徑可正常顯示與開啟（Windows）。

## 後續里程碑（留待下一版）
- 加入輕量索引（桌面/文件/下載）並與記憶點合併搜尋。  
- 加 Everything/Windows Search 即時候選（免全掃）。  
- GUI（沿用我既有的 Finding_Controller 流程）＋「✅/❌ 學習」、「➕別名」。  
- 目錄指紋 & 候選父目錄局部補掃（避免 TB 級全機掃描）。

---

交付時，請 Codex 直接照以上檔案與內容建立專案骨架、提交 PR。
