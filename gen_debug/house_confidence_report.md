# 支系关系能提升多少家族复用置信度

生成时间：2026-10-18
数据源：`dynasty_merge_map.json`（168 child → 42 parent）+ `dynasty_cross_check_loc.json`（v2 的 272 条匹配）+ vanilla CK3 的 dynasty/house/本地化

---

## 结论先说

**能，而且提升幅度很大：168 个被归并家族里，145 个（86%）拿到了新证据。**

| | 归并前（v2 口径） | 归并后（本报告） |
|---|---|---|
| 有具体 vanilla 对应物 | 8（仅强证据） | **53** |
| 其中可无损复用 | 0 | **20**（A1 结构对齐） |
| 间接支持（父/兄弟锚定） | 5（中证据） | **92** |
| 完全无证据 | 64 | **23** |

---

## 为什么之前漏了这么多：v2 的一个盲区

v2 的 272 条匹配**只处理「数字 ID 型」vanilla dynasty**（如 `11100`）。

但 vanilla 的**日本家族全部用命名 key**：

```
japanese_fujiwara         = 藤原
japanese_minamoto_seiwa   = 清和源氏
japanese_taira_kanmu      = 桓武平氏
japanese_ashikaga ...
```

这类命名 dynasty 共有 **173 个**，在 v2 里 **0 覆盖**。

而 mod 被归并的 168 个 child 里，**日本系占 84 个**（一半）。所以之前看着"一半以上无法判定"，其实是这一半根本没被检索过。

---

## 三条新证据

### E1 本地化名匹配

把 mod 家族的英文名（`zz_eu5_politics_l_english.yml`）和 vanilla 的 `dynn_XXX` 英文名（`dynasty_names_l_english.yml`）做去重音 + 长音规范化后比对。

例：`aleramici_dynasty` = "Aleramici" ↔ `dynn_Aleramicci` = "Aleramicci"

### E2 结构反推（本报告最有效的一招）

如果某个 parent 下**多个 child 的 vanilla house parent 都指向同一个 dynasty**，那这个 parent 就是它。

例：`robertian_dynasty` 没有本地化名，但它的 child `capet` 和 `dreux` 在 vanilla 都挂在 `743 (Robertine)` 下 → `robertian = 743`。
`aleramici_dynasty` 同理：`carretto`/`ceva`/`lancia` 都挂 `206 (Aleramicci)` → `aleramici = 206`。

### E3 史实映射（日本源氏/平氏）

| mod | vanilla | 依据 |
|---|---|---|
| `seiwa_genji_dynasty` | `japanese_minamoto_seiwa` | 清和源氏 = Seiwa Genji |
| `uda_genji_dynasty` | `japanese_minamoto_uda` | 宇多源氏 = Uda Genji |
| `saga_genji_dynasty` | `japanese_minamoto_saga` | 嵯峨源氏 = Saga Genji |
| `murakami_genji_dynasty` | `japanese_minamoto_murakami` | 村上源氏 = Murakami Genji |
| `taira_dynasty` | `japanese_taira_kanmu` | 平氏（桓武平氏，最主流） |

---

## 分级结果（168 个 child）

| 级别 | 数量 | 含义 |
|---|---|---|
| **A1 结构对齐** | **20** | vanilla 本来就是 house，且父宗族一致 → 可无损复用 house key |
| **B1 父宗族冲突** | **5** | vanilla 有同名 house，但挂在别的宗族下 → 同姓不同流，需裁决 |
| **B2 结构降级冲突** | **28** | vanilla 认为它是独立 dynasty，mod 已降成支系 → 需选路线 |
| **C 间接支持** | **92** | 靠 parent 锚定 / 兄弟强证据传递 |
| **D 无新证据** | **23** | 仍然无法判定 |

---

## A1：20 个可无损复用（最可信）

这些在 vanilla 里**本来就是 house**，且父宗族与 mod 的归并结果一致。可以直接把 mod 的 house 定义删掉，改用 vanilla 的 house key。

### 日本系（12 个）

| mod house | → vanilla house | vanilla 父宗族 |
|---|---|---|
| `house_chiba` | `house_taira_chiba` | japanese_taira_kanmu |
| `house_houjou` | `house_taira_hojo` | japanese_taira_kanmu |
| `house_kaneko` | `house_taira_kaneko` | japanese_taira_kanmu |
| `house_miura` | `house_taira_miura` | japanese_taira_kanmu |
| `house_irie` | `house_kudo_irie` | japanese_kudo |
| `house_kikkawa` | `house_kudo_kikkawa` | japanese_kudo |
| `house_nikaidou` | `house_kudo_nikaido` | japanese_kudo |
| `house_ishikawa` | `house_minamoto_ishikawa` | japanese_minamoto_seiwa |
| `house_toki` | `house_minamoto_toki` | japanese_minamoto_seiwa |
| `house_sasaki` | `house_minamoto_sasaki` | japanese_minamoto_uda |
| `house_watanabe` | `house_minamoto_watanabe` | japanese_minamoto_saga |
| `house_shijou` | `house_fujiwara_shijo` | japanese_fujiwara |

### 欧洲/拜占庭（7 个）

| mod house | → vanilla house | vanilla 父宗族 |
|---|---|---|
| `house_capet` | `house_capet` | 743 Robertine |
| `house_dreux` | `house_dreux` | 743 Robertine |
| `house_carretto` | `house_carretto` | 206 Aleramicci |
| `house_ceva` | `house_ceva` | 206 Aleramicci |
| `house_lancia` | `house_lancia` | 206 Aleramicci |
| `house_komnenos_doukas` | `house_komnenos_doukas` | 195 Angelos |
| `house_plantagenet` | `house_plantagenet` | 723 Anjou |
| `house_urgell` | `house_urgell` | 100204 Barcelona |

> 注意：`taira_dynasty` 在 vanilla 有 4 个分流（kanmu/koko/montoku/ninmyo），mod 只有一个 taira。默认取 kanmu（桓武平氏）最合理，但严格说要按具体支系分流。
> 同理 `fujiwara_dynasty` 在 vanilla 有 `japanese_fujiwara`（本家）和 `japanese_fujiwara_oshu`（奥州藤原）两个，mod 的应取本家。

---

## B1：5 个历史分歧，必须你裁决

这几个 vanilla 有同名 house，但**挂在别的宗族下**，说明 vanilla 和你认定的血缘不同。

| mod 家族 | 你归到 | vanilla 挂在 | 问题 |
|---|---|---|---|
| `ashikaga` 足利 | 清和源氏 | `house_fujiwara_ashikaga` → 藤原 | 日本史上有两个足利：藤原秀郷流 vs 源义国流（尊氏那支）。vanilla 取了藤原流，你取了源流 |
| `hatakeyama` 畠山 | 清和源氏 | `house_taira_hatakeyama` → 桓武平氏 | 畠山氏主流是平氏（平氏畠山），vanilla 可能更准 |
| `hiraga` 平贺 | 藤原 | `house_minamoto_hiraga` → 清和源氏 | 平贺氏是源氏（源氏平贺），vanilla 可能更准 |
| `armagnac` 阿马尼亚克 | `lomagne` | `house_armagnac` → 388 Vasconia | mod 的 lomagne 是否就是加斯科涅系？ |
| `chalon` 沙隆 | `ivree` 伊夫雷亚 | `house_chalon` → 733 Auvergne | 沙隆家族与奥弗涅、伊夫雷亚的关系 |

**这 5 个不是"置信度不够"，是"两个来源说法相反"。** 需要你按史实拍板。

---

## B2：28 个结构冲突（不是错，是取舍）

这些在 vanilla 里是**独立 dynasty**（有自己的 ID / 命名 key），但 mod 刚把它们降成了支系。

### 法国卡佩系（10 个）

`anjou`、`artois`、`bourbon`、`burgundy`、`valois`、`montfort`、`courtenay`、`champlitte`、`sully`、`beaumont`

vanilla 把它们做成独立 dynasty，是因为游戏起点是 867/1066——那时卡佩还没分化出这些支系。mod 是 1337 起点，做成支系**更符合历史**。

### 日本（14 个）

`gotou`、`hata`、`ii`、`ise`、`itou`、`katou`、`kikuchi`、`matsura`、`miyoshi`、`nasu`、`oouchi`、`togashi`、`toshima`、`yuasa`

vanilla 有 `japanese_goto`、`japanese_ise` 等独立 dynasty，mod 却把它们降成支系。

### 其他（4 个）

`laskaris`、`palaiologos`、`peralta`、`trastamara`

### 这意味着什么

- **想最大化复用 vanilla**：放弃这些归并，直接用 vanilla 的独立 dynasty ID。
- **想保留归并结构**：这些 house 不能复用 vanilla 的 dynasty ID，但 **name 字段可以复用 vanilla 的 `dynn_XXX` 本地化 key**（这样至少名字、颜色、纹章来源统一）。

---

## C：92 个间接支持

这些自己没找到同名 house/dynasty，但父宗族或兄弟支系已锚定，所以归并关系本身是可信的。

按宗族分布：

| parent | 支系数 | vanilla 锚定 | 说明 |
|---|---|---|---|
| `seiwa_genji` 清和源氏 | 29 | japanese_minamoto_seiwa | 足利、细川、今川、武田、南部、毛利… |
| `taira` 平氏 | 20 | japanese_taira_kanmu | 织田、小早川、相马、武藏… |
| `fujiwara` 藤原 | 19 | japanese_fujiwara | 上杉、大炊御門、姊小路… |
| `robertian` 罗贝尔 | 11 | 743 Robertine | 安茹、瓦卢瓦、波旁、勃艮第… |
| `kudou` 工藤 | 6 | japanese_kudo | 长野、相良 |
| `uda_genji` 宇多源氏 | 6 | japanese_minamoto_uda | 六角、京极、末次… |
| `aleramici` 阿莱拉米奇 | 5 | 206 Aleramicci | del Vasto |
| `kondou` 近藤 | 4 | japanese_kondo | 大平、大友、少弐… |
| `saga_genji` 嵯峨源氏 | 4 | japanese_minamoto_saga | 山城 |
| `saitou` 斋藤 | 4 | japanese_saito | 远山 |
| `tatara` 多々良 | 4 | japanese_tatara | 三木田、末、鹫津 |
| `murakami_genji` 村上源氏 | 3 | japanese_minamoto_murakami | 赤松、北畠、名和 |
| `ooe` 大江 | 3 | japanese_oe | 毛利（大江系）、长井、寒河江 |
| `hatano` 波多野 | 2 | japanese_hatano | 松田、和智 |
| `oyama` 小山 | 2 | japanese_oyama | 长沼、结城 |
| `takashina` 高階 | 2 | japanese_takashina | 高、南 |
| `yamato` 大和 | 1 | japanese_yamato | 宗像 |
| `orsini` 奥尔西尼 | 3 | 2, 7215 | apostolico/aldobrandeschi/monterotondo |
| `hohenzollern` | 2 | 12476 | hohenberg, nurnberg |
| `blois` | 2 | 721 | champlitte, sully |
| `angelos` | 2 | 195 | palaiologos |
| `barcelona` | 2 | 100204, 629 | fadrique |
| `anjou_jerusalem` | 2 | 723, 81 | lancaster |
| `subic` | 1 | 100467, 18005 | zrinski |

---

## D：23 个仍然无证据

这些父宗族也没锚定，自身也没同名匹配：

`al_ali`、`pelagia`、`waga`、`welfen`、`burgundy_castile`、`cerda`、`enriquez_castile`、`doi`、`tokunou`、`montfort_bregenz`、`date`、`hienuki`、`isa`、`ano`、`oogimachisanjou`、`kubadids`、`ijuuin`、`niiro`、`komnenos_asen`、`hatta`、`kii`、`takou`、`celjiski`

其中：
- `date`（伊达）、`hienuki`（稗贯）、`isa`（伊佐）挂 `nakamura`（中村），vanilla 没有 `japanese_nakamura` 独立 dynasty（只有 `house_fujiwara_nakamura`）
- `ijuuin`、`niiro` 挂 `shimazu`（岛津），vanilla 没有 `japanese_shimazu`
- `hatta`、`kii`、`takou` 挂 `utsunomiya`（宇都宫），vanilla 没有 `japanese_utsunomiya`
- `ano`、`oogimachisanjou` 挂 `sanjou`（三条），vanilla 没有 `japanese_sanjo`

这些宗族在 vanilla 里确实没有对应物，只能保留 mod 自定义。

---

## 42 个 parent 的锚定情况：27/42

已锚定（27 个）：

| parent | 证据 | vanilla |
|---|---|---|
| `seiwa_genji` | 史实 | japanese_minamoto_seiwa |
| `taira` | 史实 + 名匹配 | japanese_taira_kanmu（+koko/montoku/ninmyo） |
| `fujiwara` | 名匹配 | japanese_fujiwara（+oshu） |
| `robertian` | 结构反推 ×2 | 743 Robertine |
| `kudou` | 名匹配 | japanese_kudo |
| `uda_genji` | 史实 | japanese_minamoto_uda |
| `aleramici` | 结构反推 ×3 | 206 Aleramicci |
| `kondou` | 名匹配 | japanese_kondo |
| `saga_genji` | 史实 | japanese_minamoto_saga |
| `saitou` | 名匹配 | japanese_saito |
| `tatara` | 名匹配 | japanese_tatara |
| `murakami_genji` | 史实 | japanese_minamoto_murakami |
| `ooe` | 名匹配 | japanese_oe |
| `orsini` | 名匹配 + v2 | 2, 7215 |
| `angelos` | 名匹配 + v2 | 195 |
| `anjou_jerusalem` | v2 | 723, 81 |
| `barcelona` | 名匹配 + v2 | 100204, 629 |
| `blois` | 名匹配 + v2 | 721 |
| `hatano` | 名匹配 | japanese_hatano |
| `hohenzollern` | 名匹配 + v2 | 12476 |
| `oyama` | 名匹配 | japanese_oyama |
| `takashina` | 名匹配 | japanese_takashina |
| `antelminelli` | v2 | 101817 |
| `de_brienne` | 名匹配 | 80 |
| `lomagne` | 名匹配 + v2 | 5100 |
| `subic` | 名匹配 | 100467, 18005 |
| `yamato` | 名匹配 | japanese_yamato |

未锚定（15 个）：`ivree`、`nakamura`、`utsunomiya`、`kawano`、`sanjou`、`shimazu`、`al_fadl`、`asturleonesa`、`chuujou`、`deste`、`montfort_feldkirch`、`seljukids`、`sratsimir`、`vatatzes`、`zovneski`

这些在 vanilla 里没有可靠对应物（或名字差异过大无法确认）。

---

## 产物文件

| 文件 | 内容 |
|---|---|
| `gen_debug/house_confidence_v4.txt` | 完整分级报告（A1/B1/B2/C/D 全清单 + parent 明细） |
| `gen_debug/house_confidence_v4.json` | 结构化数据，供后续脚本使用 |
| `gen_debug/house_confidence_v4.py` | 分析脚本（可重跑） |
| `gen_debug/house_confidence_v2.txt` | 中间版（未加文化圈过滤，含误配，仅留档） |

---

## 建议的下一步（等你确认）

1. **A1 的 20 个**：可以立即改成引用 vanilla house key，零风险。
2. **B1 的 5 个**：需要你按史实裁决（足利、畠山、平贺、阿马尼亚克、沙隆）。
3. **B2 的 28 个**：需要你选路线——是保留归并（放弃复用 dynasty ID），还是放弃归并（直接复用）。
4. **taira / fujiwara 的多候选**：需要你决定是否按具体支系分流（如伊势平氏 vs 坂东平氏）。
