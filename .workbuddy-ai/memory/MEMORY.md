# 项目长期记忆（EU5_Modern_Borders_noshape）

## CK3 数据结构约定（从踩坑中确认）

- **dynasty 是宗族，house 是支系**。角色指支系必须写 `dynasty_house = house_xxx`；
  写 `dynasty = house_xxx` 会让游戏去找同名 dynasty，找不到就 fallback 到 `dynn_adam`。
- **COA 按 key 自动匹配**，没有 `coat_of_arms_id` 字段。`common/coat_of_arms/coat_of_arms/` 里
  `house_xxx = <目标>` / `<dynasty_id> = <目标>` 就是挂纹章，别名形如 `house_dreux = 86`。
  别名可以指向别的 COA key 或标题 key（`house_capet = k_france`）。
- 我们的支系 key 若与 vanilla house 同名，vanilla 的 COA 会**自动生效**，不要再写覆盖，
  更不能写 `house_x = house_x` 自引用。
- 文件名 `zz_` 前缀保证在 `00_` 之后加载，覆盖生效。
- `common/dynasty_houses/zz_eu5_merged_houses.txt` 被归并成 house 的条目已注释掉，
  分析脚本要读 culture 必须从备份取。

## 生成器纪律

- 用户手改过的文件绝不覆盖；写前比对内容，无变化就连 mtime 都不动，有变化才备份。
- 生成物按 key 排序、带 BOM（CK3 的 yml 和 common 脚本都要）。
- 生成脚本默认 dry run，显式 `--apply` 才落盘。

## vanilla 数据清单（E:/SteamLibrary/steamapps/common/Crusader Kings III/game）

- `common/coat_of_arms/coat_of_arms/90_dynasties.txt` — 约 3000 个 dynasty/house COA，key 是 dynasty id
- `common/dynasties/` — 10331 个 dynasty，大量没有 COA（运行时随机生成）
- `common/dynasty_houses/` — 596 个 house
- `history/characters/` — 209 个文件 18MB，角色 `name = "Catherine"` 直接是名字
- 注意：本地化里 `japanese_*` 是命名 dynasty，欧洲多用数字 ID；**重名家族常见**
  （Bourbon 329 有 COA / 100146 没有），引用前必须按 name 键二次确认。

## EU5 角色名本地化——人名翻译的真相之源（重要约定）

- **改/补 mod 人名（含复合君主名）必须先查 EU5 自带角色名表，不要手工音译：**
  `D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game/main_menu/localization/<lang>/`
  - `character_names_dynamic_l_<lang>.yml`（~50592 条 key，11 语言齐全，含简体中文）
  - `character_names_l_<lang>.yml`（补充）
- 每个 name 部分是独立 key（`name_togha: "脱花"`、`name_timur: "帖木儿"`）；
  部分完整合成名也直接本地化（`name_ang.name_chey: "昂杰"`、`name_indra.name_bhupesvaracuda: "因陀罗普佩斯瓦拉朱达"`）。
- 中文合成规则：按 EU5 部分直接**无分隔符拼接**（脱花+帖木儿=脱花帖木儿）；英文按空格。
- EU5 偶有自己的怪译（tekuder=贴古迭儿/EN=Togoldor，john=约翰/EN=Johan，henry=亨里克/EN=Henrik），
  但既然 mod 是 EU5 转 CK3，**以 EU5 为准**。
- 修复合名脚本：`gen_debug/fix_compound_names.py`（EU5 优先）+ `gen_debug/verify_compound_names.py`。

## 已完成的分期工作

1. 168 个支系归到 42 个宗族下（`zz_eu5_merged_houses.txt`）
2. 修两处致命 bug：house 文件首行 `l_english:/n`、1781 处 `dynasty = house_` → `dynasty_house`
3. 人名本地化补齐：1382 个 `name_eu5_*` key，中英两份 yml
4. 挂 vanilla COA：29 条写入 + 6 条自动生效，共 36 个支系拿到真实纹章
5. 154 个复合君主名按 EU5 本地化重译（脱花帖木儿 等），11 语言文件全部修正
