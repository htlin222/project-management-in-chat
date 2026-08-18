# HOUSEKEEPING — 怎麼叫出這裡的 skill

這個資料夾自己帶著說明書。就算打開它的平台完全沒有裝任何東西，該知道的都在裡面。

## 說明書在哪

```
.claude/skills/init/     Claude Code / Claude 各介面會自己讀這裡
.agent/skills/init/      不綁廠商的位置，其他 agent 讀這裡
HOUSEKEEPING.md          你現在看的這份
```

兩個位置內容一樣。在 `project-management-in-chat` 這個 repo 裡它們是 symlink，指向唯一的
`init/`；在 zip 裡則是各自一份真實檔案 —— symlink 過不了 zip，解壓後會變成一個只寫著路徑
的文字檔，說明書就壞了。

## 怎麼用

**平台已經裝了這個 skill**（Claude Code、Claude app）：直接說

```
/init
上次到哪？
```

**平台沒有裝**（其他 agent、別人的電腦、只有一個對話框）：把工作區給它，然後說

```
請先讀 .claude/skills/init/SKILL.md，之後照它的規則做。
```

`SKILL.md` 是完整的操作規則，不是摘要 —— 讀完就能接手，不需要先問人。

## 兩個指令

不需要安裝任何套件，只用 Python 標準函式庫（打包／解包）和 `curl`（下載）。

```bash
# 打開一包：驗檔、檢查檔名有沒有在路上被吃掉、解開、git fsck、把手動改的內容補進 commit
python3 .claude/skills/init/scripts/open.py <url 或 zip 路徑>

# 封存一包：commit、打 tag、連 .git 一起打包、再把包解開驗一次
python3 .claude/skills/init/scripts/release.py <專案資料夾>
```

`open.py --refresh-skill` 會把說明書換成目前環境裝的版本。平常不會覆寫 —— 你在別的平台
改過的說明書留著，只會提示哪幾個檔案不一樣。

## 三條不能破的規則

1. **不要用 `zip` 指令打包。** 它不設 UTF-8 旗標，中文檔名會無聲消失（`demo-專案/筆記.md`
   變成 `demo-/.md`），而且用 `unzip` 測試看不出來。一律用 `release.py`。
2. **`.git` 一定要在 zip 裡。** 沒有它，兩個版本只能當文字比對，沒有共同祖先就分不出「新增
   的行」和「對方刪掉的行」。這是唯一救不回來的錯。
3. **只新增，不覆寫。** 回存永遠是傳一個新的日期檔名進資料夾，不要蓋掉舊的。蓋掉是無聲的，
   多一個檔案是看得見的，而看得見的東西才有辦法合併。

細節在 `SKILL.md` 和 `references/`：`transport.md`（怎麼進出）、`permissions.md`（連接器權限）、
`merging.md`（兩個版本都有進度時怎麼合）。
