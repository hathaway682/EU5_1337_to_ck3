---
name: ck3-title-rebind
description: 把某个国家「改绑」到另一个头衔——公国级（首都所在的公国）或王国/帝国级（恢复王国、升王国、换掉旧键，如德里苏丹国→e_hindustan、西西里→k_trinacria）。三处一起动：eu5_ck3_title_map.csv 的 ck3_key、history/titles 的世系、_title_overrides.csv。当用户说「某国没改绑到 XX 公国」「米兰应该是伦巴第」「德里苏丹国戴印度斯坦」「西西里改成特里纳克里亚」「恢复王国」「按首都公国改绑」时使用。关键词：改绑、rebind、title_map、ck3_key、首都公国、王国、帝国、印度斯坦、e_hindustan、k_trinacria、重挂历史、capital duchy。
agent_created: true
---

# CK3 头衔改绑（rebind）

## 用途

把一个国家的头衔从当前键换到另一个键，**三处必须一起动**，少一处就出错：

1. **`gen_debug/eu5_ck3_title_map.csv` 的 `ck3_key`** —— tag → 头衔的绑定。`_gen_eu5_coa.py`
   （纹章）、`_coa_probe.py`、`_strip_county_past_history.py` 都读这张表。
2. **`history/titles/*.txt` 的世系** —— 旧块整条 reign list 重挂到新键的块。
3. **`gen_debug/_title_overrides.csv` 的 `country/title_key`** —— 让 `_patch_title_history.py`
   的 `ckey()` 也认新键。

改绑分两种，判据完全不同，别混：

| | 公国级改绑 | 王国 / 帝国级改绑 |
|---|---|---|
| 触发 | 「拿到了首都所在的公国」 | 命名 / 历史决策，用户指定 |
| 判据 | `_grant_landed_duchies` 的 `grants` + `why` | **没有推导规则**，看目标键存不存在 |
| 等级 | d → d | 可以变（k → e 也算） |
| 典型 | MLO→`d_lombardy`、GEN→`d_liguria` | DLH→`e_hindustan`、SIC→`k_trinacria` |

## 为什么不能靠重新生成

`_export_title_map.py` 算 `ck3_key` 用的是 `f"{rank}_eu5_{tag}"`，**不查 override 表**，所以
任何非等级推导的绑定它都算不出来——重跑它只会把 `d_eu5_mlo` 再写回来，也会把
`e_hindustan` 写回 `k_eu5_dlh`。同理 `_patch_title_history.py` 只认同名改绑
（`grant_why == "same name"`），米兰的伦巴第是按 `control 6/9` 发的，它不会改。
**这张表只能手改（用本 skill 的脚本）。**

## 何时使用

- 「米兰没改绑到伦巴第 / 热那亚应该是利古里亚 / 基辅应该是右岸乌克兰」
- 「得到了自己首都所在公国的国家，把历史改挂过去」
- 「德里苏丹国戴印度斯坦帝国 / 西西里改成特里纳克里亚 / 阿尔巴尼亚和马略卡恢复王国 /
  立陶宛升王国」
- 需要批量核对：哪些 rank=d 的国家拿到了首都公国、却还戴着 `d_eu5_<tag>` 空壳

## 公国级改绑的判定口径（血泪）

- **只对真的拿到了这个公国的国家**（`_grant_landed_duchies.compute()` 的 `grants`），
  不是「首都恰好落在某个公国里」。后者会命中 162 个国家，绝大多数没拿到那个公国。
- **只对真实绑定是公国（`d_`）的国家**。王国/帝国不降级：阿拉贡是 `k_aragon`、马略卡
  override 到 `k_mediterranean_sea`、埃雷特纳 `k_eretnid`、奥斯曼 `k_ottoman`——它们在
  title_map 里可能还残留 `d_eu5_*` 旧行，但那是过期的，不是公国。
- **同名改绑**（公国名 = 国名，`grant_why == "same name"`）已经由 `_patch_title_history.py`
  处理，本 skill 只在校准 title_map（`--sync`）时把那一行的 `ck3_key` 对齐。

## 王国 / 帝国级改绑（如印度斯坦）

这一档**没有「首都公国」那样的推导规则**，改到哪个键是命名/历史决策，由用户拍板
（记录在 `_title_overrides.csv` 的备注里）。要做的是把键改对、把历史搬对、把空壳清掉。

**第一步：确认目标键真的存在，并搞清它是什么。**

```bash
grep -rn "^e_hindustan = {\|^	k_trinacria = {" common/landed_titles/*.txt
```

三种来源，处理方式不同：

| 来源 | 在哪 | 例子 | 能不能删 |
|---|---|---|---|
| CU 1337 法理树 | `00_landed_titles.txt`（嵌套在 e_/k_ 下） | `k_trinacria`、`k_lithuania`、`k_delhi` | **不能删**，是世界的真实头衔 |
| CU 自带 titular | `zz_eu5_titular.txt` 顶层 | `e_hindustan`、`k_albania`、`k_mediterranean_sea` | 别删，别人可能还要戴 |
| 本 mod 铸的壳 | `X_eu5_TAG` | `d_eu5_mlo`、`k_eu5_alb` | 换掉后删块 + 删声明 |

**第二步：等级可以变，`ck3_tier` 必须跟着改。** DLH 的旧绑定是 `k_delhi`（王国），新键
`e_hindustan` 是帝国，行里的 `ck3_tier` 要从 `k` 改成 `e`。脚本会按新键首段自动写。

**第三步：旧键的处理分两种，这是最容易搞错的地方。**

- 旧键是 **CU 法理树里的头衔**（`00_landed_titles.txt`，如 `k_delhi`、`d_liguria`）→
  **只挪绑定，块和声明都不许删**。德里这个法理王国在 CU 里是存在的，DLH 不戴它，别人
  还可以戴；删了声明就是从这个世界的法理树上挖掉一个王国。热那亚改戴 `k_genoa` 之后
  `d_liguria` 仍归它持有（世系里 holder 不变），只是不再是主头衔。脚本会打印
  `old key is a CU de jure title: binding only` 并跳过合并与删除。
- 旧键是 **伯爵领 / 男爵领**（`c_` / `b_`，如比萨的 `c_pisa`）→ 同上，**只挪绑定**。
  这是真领地，改名或删除会让那片地直接没有领主。比萨从 `c_pisa` 改戴 `k_pisa` 后，
  它照样持有 `c_pisa`，只是主头衔变成王国。
- 旧键是 **本 mod 铸的空壳**（`X_eu5_TAG`，或 `zz_eu5_titular.txt` 里没人戴的 titular，
  如 `k_sicily`）→ 删块 + 删 `zz_eu5_titular.txt` 里的声明，否则 ledger 里永远留一个
  有 capital、没 holder 的空壳（`k_sicily` 现在就是：第 1195 行，`capital = c_mazara`，
  没有历史块）。

**新键有没有块，决定怎么搬世系：**

- 新键**已有块**（如 `k_trinacria` 有人戴过）→ 按日期合并旧块世系、去重、保留 1337 条；
- 新键**没有块**（法理头衔，从来没人戴，如 `k_africa`、`k_tahert`）→ **整块搬过去**：
  旧块连同它的 `1337.4.1` 条目原样改名成新键，位置不变，打印
  `carry the whole block over (N reigns)`。法理头衔本身不需要 history 就能存在，
  块是「谁戴过」的记录，搬过去正好。

**`capital` 字段不要跟着改。** 那是头衔自己的法理首府（`e_hindustan` 的
`capital = c_delhi`），不是国家的首都；国家的首都由 province history 决定。

**必须写 override，备注不许乱写。** 王级改绑 100% 靠 override 存活：没有它，
`_export_title_map.py` 重跑会写回 `{rank}_eu5_tag`，`_patch_title_history.py` 也会按旧
ckey 重铸旧壳。脚本按新键首段自动写「改绑到帝国/王国/公国 `<key>`（原 `<旧键>`）」——
**王国头衔的备注里绝不能出现「首都所在公国」**，那是公国级改绑的说法。

**改第二次时，旧 override 必须改写而不是跳过。** 热那亚先改到 `d_liguria`（首都公国），
后来又改到 `k_genoa`，如果脚本只在「该 tag 没有 override 行」时追加，第 68 行会一直停在
`d_liguria`，下一次 `_patch_title_history.py` 就把它拖回去。脚本现在会就地改写值不同的
那一行（`overrides updated: 1`），备注里的「原」取的是被替换掉的旧值。

现有 5 条是范例：

```
country,DLH,title_key,e_hindustan,用户指定：德里苏丹国戴印度斯坦帝国（原 k_delhi）
country,SIC,title_key,k_trinacria,用户指定：西西里戴特里纳克里亚（原 k_sicily）
country,ALB,title_key,k_albania,恢复王国：原版有 k_albania，不新铸 k_eu5_alb
country,MLL,title_key,k_mediterranean_sea,恢复王国：用原版 FP2 的地中海王国
country,LIT,title_key,k_lithuania,升王国：用原版 de jure 王国 key
```

## 重挂世系的硬规则

- 把旧块**整条世系按 `(年,月,日)` 数值**插进新块，**保留新块 1337.4.1 那条**（它带
  `government` / `liege`，不能覆盖）。
- 旧块里和新块同 `(日期, holder)` 的条目**去重**，否则会出现两条 `1337.4.1`。
- 删旧块、删 `zz_eu5_titular.txt` 里旧键的声明（**仅当旧键是本 mod 铸的壳**；CU 法理树
  和 CU titular 的键不动，见上一节）。
- **绝不能「新块已存在就丢旧块」**——新块常只有 1 条开局，旧块有整条世系（2026-10-28 中华/
  金帐世系就是这么丢的）。
- **改名旧键陷阱**：CSV / 清单里的 `title_key` 常常是改名前的旧键（SIC 记 `k_sicily`、
  DLH 记 `k_delhi`）。给旧键补内容 = 同一世系在新旧键各写一遍。动手前先过
  `_title_overrides.csv`：`override[tag] != 该键` 就说明这行是旧键，跳过。

## 用法

```bash
MOD="D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"
EXP="D:/Documents/Paradox Interactive/Crusader Kings III/mod/Global_modern_map/eu5_export"
SK="<MOD>/.workbuddy-ai/skills/ck3-title-rebind/rebind.py"

# 批量：所有「拿到首都公国、但绑定仍是 d_eu5_*」的 rank=d 国家
python "$SK" --mod "$MOD" --export "$EXP" --all-capital-duchy --dry-run   # 先看清单
python "$SK" --mod "$MOD" --export "$EXP" --all-capital-duchy

# 单个公国：显式指定目标 key
python "$SK" --mod "$MOD" --export "$EXP" --tag MLO --to d_lombardy --dry-run
python "$SK" --mod "$MOD" --export "$EXP" --tag MLO --to d_lombardy

# 王国 / 帝国：目标和等级都显式给（脚本按新键首段写 ck3_tier）
python "$SK" --mod "$MOD" --export "$EXP" --tag DLH --to e_hindustan --dry-run
python "$SK" --mod "$MOD" --export "$EXP" --tag SIC --to k_trinacria --dry-run

# 一次改多个、各自目标不同：用 --map TAG=KEY（--to 只有一个值，会套到所有 --tag 上）
python "$SK" --mod "$MOD" --export "$EXP" --map TUN=k_africa --map TLE=k_tahert --dry-run
```

`--to` 的目标键**必须已在 `common/landed_titles/` 声明**，否则整行跳过并报
`target key NOT declared - skipped`。绑到一个不存在的键，游戏里就是空绑定。

### `--sync`：只校准 title_map（不动历史）

历史已经挂对了、只有 `ck3_key` 还写着旧键时用它。它按下面的顺序算每个国家的**真实绑定**，
和目标键不一致才改那一行（顺带刷新 `ck3_tier` / `ck3_holder` / `ck3_liege` /
`ck3_government` / `ck3_declared`）：

1. `_title_overrides.csv` 里的 `title_key` —— 王国/帝国/公国的裁决，压过一切等级推导。
   **王级改绑（DLH/SIC/ALB/MLL/LIT）就是靠这一条被 `--sync` 认出来的**；
2. `rank == d`：同名公国 → 首都所在公国 → 都不成立就**不动**；
3. `rank == d` 且出现在 `--vassals-of <TAG>` 的附庸名单里（`eu5_politics.json` 的
   `dependencies`，`type == vassal`）→ 拿回 `d_eu5_<tag>`，即「被附庸降级为伯国的公国」；
4. `rank == k/e`：`{rank}_eu5_<tag>`（教皇国例外 `k_papal_state`）。

```bash
# 立陶宛升王国后，它那些被降成伯国的附庸公国一起拿回自己的公国
python "$SK" --mod "$MOD" --export "$EXP" --sync --vassals-of LIT --dry-run
python "$SK" --mod "$MOD" --export "$EXP" --sync --vassals-of LIT
```

两条保险，别去掉：

- **0 个县（`held == 0`）的 d/k/e 不动** —— 它的等级头衔已被丢弃，硬拉回公国等于凭空造空壳。
- **目标键没在 `common/landed_titles/` 声明就不写** —— 绑到一个 dropped 的键，游戏里是空绑定
  （实例：SWB 的 `d_eu5_swb` 在 `eu5_titles_dropped.txt` 里，`--sync` 会把它列进
  「skipped, target key not declared」而不是改坏）。

`--vassals-of` 必须显式给：`rank == d` 的兜底**不做** `d_eu5_<tag>` 推断，否则所有
rank=d 的国家（包括跟这条规则无关的不伦瑞克、萨克森-维滕贝格）都会被拉回公国。
**附庸关系只认 `dependencies`，不许凭名字或「都是 rank=d」推断。**

脚本幂等：旧键从 title_map 当前 `ck3_key` 读，跑第二遍会显示「already bound」，
只补 title_map / override，不重复并世系。

## 改完必查（封臣关系是重灾区）

**1. 悬空的 `liege`。** 改绑删掉旧键的块和声明之后，所有写着 `liege = <旧键>` 的县都指向
一个不存在的头衔，封臣关系**静默断掉**（不报错，游戏里就是独立了）。普鲁士那次最明显：
TEU 改到 `d_prussia` 后，`c_chelmno` / `c_lower_prussia` / `c_warmia` 还写着
`liege = d_eu5_teu`，萨姆兰（SMD）直接挂空。脚本现在会自动改（`liege_map[old] = new`，
全文 `liege = 旧键` → `liege = 新键`），但**改完必须再扫一遍**：

```bash
python3 gen_debug/_fix_dangling_liege.py . --dry-run   # 必须输出 0
```

**2. 主头衔没有块 → 国家自己丢了宗主。** 新键是 landless titular、从来没人戴过（如
`k_genoa`、`k_pisa`）时，它没有 history 块，也就没有 `liege` 行，热那亚和比萨会直接
从 HRE 独立出去。这类要补一个 1337 块：

```
k_genoa = {
	1337.4.1 = {
		holder = gen_galeotto_spinola
		government = republic_government
		liege = e_hre
	}
}
```

**3. 结构校验。**

```python
import io, re, collections
# 1) 括号平衡、无裸 LF
raw = io.open("history/titles/zz_eu5_titles.txt","rb").read()
t = raw.decode("utf-8-sig").replace("\r\n","\n")
print("braces", t.count("{")-t.count("}"), "bare LF", raw.count(b"\n")-raw.count(b"\r\n"))
# 2) 新块世系条数 = 旧块条数（除同日期去重），且无重复日期
# 3) 旧键块、旧键声明都不在了（仅限本 mod 铸的壳；CU 法理树 / CU titular 不动）
# 4) title_map 该行 ck3_key = 新键，ck3_tier = 新键首段；行数不变（6963）
# 5) holder 全部能在 history/characters 找到
# 6) 王级改绑：override 里该 tag 的 title_key = 新键，且备注写明原因
# 7) 所有 liege 目标都在 common/landed_titles 里有声明
```

`_patch_title_history.py` 可以之后再跑一遍（它是安全的），它会按新 ckey 把新键的
holder / government / liege 校一遍、并归层；**绝不要跑 `_fix_politics_output.py`**。

## 注意

- 备份一律放 `F:/EU5_Modern_Borders_bak/`，项目目录不残留 `.bak`。
- 改 title_map 用 `csv` 模块读写（字段里可能有逗号），行尾保持原样，行数必须不变。
- `_title_overrides.csv` 追加前先查 tag 是否已有 `title_key` 行，避免重复。
- 王级改绑后旧键的空壳声明要单独判断：`zz_eu5_titular.txt` 里留下没历史、没绑定的
  titular（如 `k_sicily`）不会自动消失，得手工删，否则它在 ledger 里一直是个有首都的空头衔。
