# 踩过的坑

## 一、文件格式（最贵的坑）

### 1. 纯 CRLF 文件用行级正则必须容忍 `\r`

`history/provinces/00_generated_provinces.txt` 是 **UTF-8 BOM + 纯 CRLF**。

```python
# ✗ 错：newline="" 读进来每行尾带 \r，这个正则一条都匹配不上，stat 全空、误报「无变化」
raw = io.open(P, encoding="utf-8-sig", newline="").read()
re.match(r"^(\d+) = \{$", line)

# ✓ 对：先剥掉行尾的 \r
body = line[:-1] if line.endswith("\r") else line
re.match(r"^(\d+) = \{$", body)
# 插入新行要自带 \r
out.append("rite = dhyana\r")
```

skill 的 `scripts/_common.py` 已经用「按字节读 → 判断行尾符 → split/join → 按字节写」绕开了这个坑，新脚本直接用它。

### 2. 写盘后必须校验裸 LF = 0

```python
st = C.byte_stats()
assert st["lone_lf"] == 0 and st["bom"] and st["open"] == st["close"]
```

### 3. json 的 int 键读回来是字符串

```python
d = {int(k): v for k, v in json.load(f).items()}   # 不转就全是 None / '-' 或 KeyError
```

## 二、faith / rite 语义

### 4. 「有 rite 就不写 faith」

用户既定口径：省里已经有 rite 时，faith 行是多余的，**该删掉**（`rite = acharya` 的省没有 `faith =` 行就是这个原因）。

但注意：`_apply_cu_three_teachings.py` 的做法是**把 faith 行直接替换成 rite 行**，即 `faith = X` → `rite = Y`，faith 行消失。这跟上面口径一致，但会让「读 faith」的脚本读不到值——后续脚本要么从备份取，要么改从 rite 反推。

### 5. 判能不能挂看 religion，不看 faith

见 `rites.md` 第一节。基督教 9 个礼全绑在 `christian_faith` 上、省份写 `orthodox`/`catholic`，这是 vanilla 设计，**不是 bug**。曾经按 faith 严格比对，误报 1325 省。

### 6. 省只写 faith 不写 rite = 按 main_rite 回落

所以「没写 rite 行」不等于「没宗派」。当前 21034 个有 faith 的省里只有 4066 个写了 rite，剩下 16968 个全靠回落。

### 7. `confucian_faith` / `maitreya_faith` 没有 main_rite

靠 `history/faiths/00_eastern_misc.txt` 的日期块决定，1337 开局落 `daoxue` / `maitreya`。改这两个 faith 的显示时要连这个文件一起看。

### 8. 「按县判定、按省落地」是反复踩的坑

CK3 只读伯爵领**首府男爵领**（块里第一个 `b_`）的 faith/culture。所以：
- 要整县统一 → 按县判定、给县内所有省写同一个值；
- 要逐省区分 → 按省判定，别用县值覆盖。

印度教必须**整县染色**（`_apply_hindu_faith_branch.py`）。CU 铺满伯爵领也是同一逻辑。

## 三、EU5 数据源

### 9. `religion_definition = mahayana #Azhaliism` 的 `#Azhaliism` 是注释

不是第二个值，不要解析成两个宗教。

### 10. EU5 的笼统 key 靠同名匹配会吃错范围

- `shamanism` 会命中 CK3 的满洲/黑龙江通古斯萨满，导致西伯利亚中部被写错（`_apply_siberian_faith.py` 用 region 判断修正）。
- EU5 把 `tunjur`/`funj`/`fur`/`gumuz`/`kunama` 误标 `egyptian_dialect` —— 这是撒南非洲出现埃及文化/宗教的根源。
- `religion_definition` 里同一个名字可能横跨多个 sect（DAI = 儒家+净土+禅宗），**sect 身份要取 `laws` 首个元素**。

### 11. 国家宗教看 `setup/countries/*.txt`，不是 pops

pops 是人口分布，国家宗教是国教。两者不一致时按具体任务选：
- 省份层人口多数 → pops
- 教随国定（印度教支派、伊斯兰学派）→ 国家 + 国际组织

## 四、CU（CrusaderUniversalis）取数

见 `cu-source.md`，核心是四层缺一不可：`history/provinces` → 伯爵领首府铺满 → `province_mapping` 补缺 → 质心匹配。

## 五、流程纪律

### 12. 动手前先跑 `religion_audit.py`

**文件状态可能和你记忆里的不一样。** 用户会自己回滚文件（实测过一次：CU 三教转换的成果在某天被整体还原，`quanzhen` 从 19 省变 0 省）。所以任何「已知数字」都要当场核。

### 13. 改之前先打保存点

```bash
cd <MOD>/gen_debug && python _religion_checkpoint.py save 改之前
```

### 14. 非必要不全量重建

`eu5_to_ck3.py` 重跑会冲掉后面所有补丁层（原始宗教修正、rite 层、CU 层）。要改就外科手术式只改目标行（`religion_set.py`）。

### 15. 改映射要改 `CURATED`，不要改 CSV

`eu5_ck3_faith_map.csv` 是 `_build_faith_map.py` 的产物。改 CSV 下次重跑就没了。
**三处同步**：`_build_faith_map.py` 的 `CURATED` / CSV / 各 `_apply_*` 脚本里的硬编码规则表。

### 16. `_apply_faith_map.py` 会把 `gen_faith_*` 一律变 `pagan`

那是 Ck3MapGen 自己生成的程序化 faith，CK3 没有对应物，兜底 pagan 是有意为之。别以为是漏映射。

### 17. 游戏安装目录只读

`E:\SteamLibrary\steamapps\common\Crusader Kings III\game\` 和 EU5 目录**只能读**，产物一律放工作区。

### 18. 本地化从原版找

mod 的 `localization/simp_chinese/` 只覆盖少量 key。查不到就查原版 `game/localization/simp_chinese/`，都没有再问用户，**不许编名字**。
