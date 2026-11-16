# 《潮线之上（Last Landfall）》开场 CG 新版精炼方案（60 秒 · 6 镜）

> **设计原则（总结并出新）：**
> 1. **紧扣你的大纲图**：直接以 [OpeningComicIntro.png](../OpeningComicIntro.png) 的三联剧场版 2D 动画电影风与三幕冲突作为全片主干，砍掉冗长拖沓的前戏。
> 2. **控制在 60 秒（6 镜 × 10 秒）**：游戏开场 CG 一分钟刚好讲透“误判危机 → 突袭海啸 → 潮线多年上涨 → 顺信号遇沉船 → 抵达高地岛开局”全部因果，不拖泥带水。
> 3. **逻辑与画风全统一**：
>    - ChatGPT 首轮直接上传 `OpeningComicIntro.png` 作为唯一视觉基准（清晰线条、剧场版 2D 动画光影、真实建筑与海水质感）。
>    - 前 3 镜以城市与灾变宏大视角推进；后 3 镜聚焦海上生存阶段，**主角（30 岁短黑发女救援队长：褪色锈橙防水外套 + 暗红救生衣 + 左臂纯白三角布章）** 与 **橙白方正驾驶舱救援艇** 合理登场。
>    - 每个分镜内部严格**同空间推拉/延时**（先画首帧 A，再让 ChatGPT 基于 A 续画尾帧 B），彻底杜绝画面穿帮与人物变形。

---

## 全片 6 镜总览（总时长 60 秒）

| 镜号 | 时长 | 核心任务 | 与游戏设定对应 |
| :--- | :--- | :--- | :--- |
| **S01** | 10s | **虚假的胜利（晴空拦截与全城欢呼）** | 漫画第 1 格：拦截首批先导碎片，人类以为靠自己化解了危机 |
| **S02** | 10s | **盲区突袭（黑云压城与主碎片坠海）** | 漫画第 2 格：太阳盲区主碎片云突至，防线失守、连续坠入外海 |
| **S03** | 10s | **旧世界倾覆（海啸吞没沿海城市）** | 漫画第 3 格：巨型海啸毁灭海岸城市，高地幸存者无力回望 |
| **S04** | 10s | **潮线攀升与孤舟微光（多年后遗症）** | 海面多年缓涨淹没旧港；高台应急灯与小船成为唯一联系 |
| **S05** | 10s | **追寻信号遇沉船（接入开局剧本）** | 一男一女 2 人驾小艇抵近求救信号，发现目标已成搁浅沉船 |
| **S06** | 10s | **发现三岛群岛、暗毁灯塔与标题落版** | 晨雾散开现出三座分离岛屿与熄灭毁坏的灯塔废墟，镜头拉升至实机俯瞰留白出标题 |

---

## ChatGPT 总设定指令（新对话第 1 步，务必上传 `OpeningComicIntro.png`）

```text
I am creating 6 pairs of Start & End keyframes (12 images total) for a tight 60-second anime opening movie for my survival game "Last Landfall".
Use the uploaded image as the EXACT visual style, color script, and narrative backbone: theatrical 2D anime movie illustration (crisp ink linework, dramatic painted skies and ocean spray, realistic modern coastal architecture and vessels, zero muddy 3D look, zero readable text/numbers/watermarks, 16:9 widescreen).

Main character & vessel continuity anchors (appear from S04_B onward):
- Heroine: 30-year-old female maritime rescue leader, short tousled black hair, faded rust-orange waterproof jacket over a dark red life vest, dark pants, plain blank white triangular patch on her left sleeve (NO text).
- Rescue Boat: Practical weathered orange-and-white small coastal rescue boat with dark blue hull, boxy wheelhouse cabin, two round roof floodlights, and rear outboard motor.

Confirm you understand the visual style and continuity rules, then wait for S01_A.
```

---

## 分镜脚本、生图提示词与视频提示词

### S01｜00:00–00:10（10s）：虚假的胜利 —— 晴空拦截与全城欢呼

* **画面目的**：开片第一秒直接用明亮阳光与人群欢呼建立“人类以为靠防御系统战胜灾难”的松懈感，为下一秒反转攒足落差。（海边长廊直接肉眼仰望高空截击，不放多余户外屏幕。）
* **首帧 `S01_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S01_A matching the exact theatrical 2D anime style of the LEFT PANEL of the uploaded reference image.
  Scene: Bright sunlit afternoon at a modern coastal waterfront promenade overlooking a sparkling blue bay. In the upper clear blue sky framed by sunlit clouds, a crisp golden-white interception flash shatters a lone incoming meteor rock into harmless sparkling trails. In the lower foreground, a dense crowd of everyday citizens (viewed mostly from behind and three-quarter profiles) stops along the seaside railing and plaza to look directly upward at the sky burst. Modern coastal glass buildings and leafy trees line the left boardwalk—NO outdoor display screen or TV screen anywhere. Warm hopeful sunlight, crisp anime line art, NO readable text, NO logos, NO subtitles, 16:9.
  ```
* **尾帧 `S01_B`（同对话续画指令）**：
  ```text
  Generate S01_B by continuing smoothly a few seconds later from S01_A in the exact same sunny coastal waterfront promenade, crowd, and 2D anime film style, tilting the camera slightly downward and pushing gently into the crowd (still NO outdoor display screens anywhere).
  The bright interception flash in the sky has faded into a calm fading white vapor trail in blue sky. On the sunlit plaza below, people exhale in visible relief, smile warmly, clap, and embrace family members; a young woman and man in casual jackets laugh with relieved tears while looking at the calm blue sky. Clean natural anatomy, joyful human warmth, NO readable text on signs, 16:9.
  ```
* **Flow 视频提示词（`S01_A → S01_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation in crisp bright daylight, vibrant cerulean blue sky, sparkling ocean bay, and warm golden sunlit highlights. One continuous 10-second gentle camera tilt-down and subtle forward drift across the sunlit coastal waterfront promenade. High in the clear sky above the bay, a bright golden-white interception burst breaks an incoming rock cleanly into fading harmless vapor wisps; as the camera drifts into the seaside crowd below, citizens burst into relieved cheers, warm smiles, applause, and quiet embraces, believing humanity has solved the crisis. Gentle coastal breeze moving hair and jackets, smooth eased motion, no outdoor screens, no cuts, no readable text.
  ```

---

### S02｜00:10–00:20（10s）：盲区反转 —— 黑云压城，密集火雨坠入外海

* **画面目的**：瞬间把明媚色调砸进煤灰与暗橙灾难——被太阳眩光掩盖的主碎片云撕裂云层坠入外海，交代“来不及拦截、大量水汽与海啸即将生成”。
* **首帧 `S02_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S02_A matching the exact theatrical 2D anime style and composition of the CENTER PANEL of the uploaded reference image.
  Scene: High coastal hillside overlook gazing across a sprawling bay city toward the open sea horizon. The bright sky has vanished beneath heavy, churning charcoal-gray storm clouds. Dozens of blazing orange-and-gold icy rock meteors slice diagonally downward out of the dark upper clouds toward the distant ocean horizon, leaving glowing smoky trails across the sky. Windblown dark-green coastal hillside foliage frames the bottom foreground; the city sits tense and shadowed below. High drama, crisp anime shading, NO lava, NO spaceships, NO text, 16:9.
  ```
* **尾帧 `S02_B`（同对话续画指令）**：
  ```text
  Generate S02_B from the EXACT SAME coastal hillside camera angle as S02_A, seconds later, in the exact same 2D anime film style.
  Now multiple huge icy fragments have slammed into the distant outer ocean along the horizon: towering blinding-white geysers of seawater and boiling steam plumes erupt vertically from the ocean surface, casting stark pale-orange light across the dark sea and the underside of the storm clouds while more burning trails keep descending. Below the churning sea horizon, the bay begins surging darkly toward the silhouetted city. Crisp anime impact mist, NO city buildings exploding directly, NO text, 16:9.
  ```
* **Flow 视频提示词（`S02_A → S02_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation matching dramatic disaster cinema, brooding charcoal storm grays pierced by fiery orange meteor streaks and blinding white ocean impact plumes. Steady wide shot from the coastal hillside overlook with a subtle visceral camera shake as impacts hit. Dozens of blazing icy rock fragments streak rapidly down through thick dark storm clouds and slam successively into the distant outer ocean, sending colossal vertical geysers of seawater and swirling white steam towering above the horizon and flickering amber reflections across the dark sea. Wind whips the foreground hillside leaves as shockwaves ripple across the water. Smooth water physics, no cuts, no text.
  ```

---

### S03｜00:20–00:30（10s）：海啸吞没旧世界

* **画面目的**：完美还原漫画第 3 格——巨浪吞没沿海城市，确立末世降临与“低洼海岸已无法居住”的物理现实。
* **首帧 `S03_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S03_A matching the exact theatrical 2D anime style and composition of the RIGHT PANEL of the uploaded reference image.
  Scene: Elevated viewpoint on a dark rugged rocky coastal cliff covered in windswept grass. In the lower-right foreground, three ordinary survivors wearing waterproof jackets and emergency backpacks crouch on the rocks looking out over the coastal bay. Below them under dark stormy skies, coastal bridges and mid-rise waterfront buildings sit beside churning gray water as a colossal, towering wall of dark teal tsunami wave crowned with roaring white foam rises massively over the distant sea wall, poised to crash across the city. Crisp anime foam and spray detail, NO gore, NO text, 16:9.
  ```
* **尾帧 `S03_B`（同对话续画指令）**：
  ```text
  Generate S03_B by pulling the camera slightly back and tilting subtly down on the exact same cliff and city from S03_A in the 2D anime film style.
  The colossal foaming tsunami has surged deep across the coastal city below, flooding streets and wrapping roaring white currents and muddy sea foam around concrete mid-rise buildings, submerged highway ramps, and rocky sea stacks while heavy rain mist sweeps the bay. On the high rocky ledge in the lower-right foreground, the three backpacked survivors brace against the gale, watching silently as the waterfront sinks beneath the tide. Realistic scale, NO corpses, NO readable signs, 16:9.
  ```
* **Flow 视频提示词（`S03_A → S03_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, cold stormy slate-blue, deep churning teal water, and crisp roaring white foam. One continuous 10-second slow camera pull-back behind the crouched backpacked survivors on the wet rocky cliff overlooking the coastal city. The colossal wall of foaming ocean water surges relentlessly over the sea wall, crashing across bridges and swirling around concrete apartment blocks in heavy torrents of muddy spray and mist. Fierce sea wind whips the grass and raincoats in the foreground as rain begins sweeping the air. Weighty realistic water momentum, no cuts, no sudden morphing, no gore, no text.
  ```

---

### S04｜00:30–00:40（10s）：潮线多年缓慢攀升，只剩短波与小船

* **画面目的**：用一镜“时间流逝”讲清本作核心前提——灾难不是一次结束，富冰碎屑带来持续降雨与水量，**海平面逐年缓慢上涨**；旧城区逐年没顶，通信中断后人们改用短波电台与小型救援船。
* **首帧 `S04_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S04_A in the exact same theatrical 2D anime film style.
  Scene: Fixed elevated view looking along a flooded coastal harbor town street and a high concrete sea wall below an upper rocky terrace. Just after the disaster under gloomy overcast sky, muddy water sits at street-curb height, leaving soaked storefronts, rusted lampposts, and wet wooden mooring posts visible above water. Up on the safe upper concrete terrace at left stands a low utilitarian stone rescue shed with a shortwave radio mast; a faint amber light glows inside its small window. Distant misty mountain ridges frame the bay. Clean anime architectural detail, NO readable text or numbers, 16:9.
  ```
* **尾帧 `S04_B`（同对话续画指令）**：
  ```text
  Generate S04_B from the EXACT SAME fixed camera position, terrace, rescue shed, and distant hills as S04_A, depicting several years later in the same 2D anime film style.
  The calm deep-teal ocean has risen steadily by several meters: pale salt marks and green algae now line the upper sea wall just below the terrace; the street, lampposts, and lower floors of the coastal buildings are completely submerged beneath quiet glassy water, with only rooftops peeking out. Passing smoothly through the flooded waterway in the right midground is our small weathered orange-and-white rescue boat (dark blue hull, boxy wheelhouse cabin with two round roof floodlights lit softly in misty rain, tiny glowing green shortwave light inside the cabin). Melancholic passage of time, NO text, 16:9.
  ```
* **Flow 视频提示词（`S04_A → S04_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, fixed-camera multi-year time-lapse across shifting seasons of gray rain, pale mist, and cool winter teal light. The camera holds completely steady on the coastal harbor street and concrete sea wall with only a faint slow breath-like drift. Over 10 seconds, rain clouds sweep overhead and seasons dissolve gently as the sea level creeps steadily upward year by year along the stone wall—gradually swallowing rusted lampposts, doorways, and mooring posts while salt stains climb higher—until the old town rests quietly half-submerged under calm deep-teal water. Near the end, a small orange-and-white boxy-cabin rescue boat glides smoothly past through the flooded street with warm twin roof lights glowing softly in the mist. Smooth gradual water rise, no sudden waves, no morphing buildings, no cuts, no text.
  ```

---

### S05｜00:40–00:50（10s）：顺短波信号出航，遇见沉船

* **画面目的**：直接落地到玩家开局配置——**严格只有一男一女共 2 人 + 1 艘小救援艇 + 物资**，顺着求救信号出航调查，抵达后发现目标已成**沉船**（对应东副岛沉船设定与剧本开局）。
* **首帧 `S05_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S05_A in the exact same theatrical 2D anime film style.
  Scene: Low three-quarter stern tracking view right behind our weathered orange-and-white small coastal rescue boat (dark blue hull, boxy wheelhouse cabin, two round roof lights glowing softly, rear outboard engine pushing a crisp white wake) cutting smoothly through misty deep-teal morning waves. STRICTLY ONLY TWO PEOPLE ON THE BOAT (one woman + one man): inside the open rear cabin doorway, our Heroine (30yo woman, short black hair, faded rust-orange waterproof jacket, dark red life vest, plain blank white triangular patch on left sleeve) stands steering at the helm; sitting alone on the open rear deck beside strapped waterproof supply crates and toolboxes is ONE male technician crewmate in a muted slate-gray/sage waterproof jacket and light tan life vest (NO third person anywhere on board). Ahead in the misty right midground rests the tilted, rusted half-sunken hull of an abandoned shipwreck stranded on dark sea rocks. Thick morning fog hides the far horizon. NO readable text, 16:9.
  ```
* **尾帧 `S05_B`（同对话续画指令）**：
  ```text
  Generate S05_B by continuing smoothly forward past the shipwreck from S05_A in the exact same 2D anime film style.
  Keep STRICTLY THE EXACT SAME TWO PEOPLE ONLY on the boat (one woman steering inside the cabin + one man sitting on the rear deck by the supply crates—NO third person). The orange-and-white rescue boat has steered slightly past the silent half-submerged shipwreck (now passing behind on the right) into clearer water as pale silver morning fog parts ahead. Breaking through the distant slate clouds is a soft beam of warm amber dawn sunlight, revealing the silhouettes of THREE separate green-and-rocky highland islands emerging across ocean channels in the mist ahead (a large central main island and two smaller flanking satellite islands). Quiet hope, NO modern buildings, NO text, 16:9.
  ```
* **Flow 视频提示词（`S05_A → S05_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, cool misty morning sea tones opening toward a soft golden-amber break in the clouds. One continuous 10-second low tracking shot following just behind the small weathered orange-and-white rescue boat as it rides gentle ocean swells with realistic bobbing and white wake spray. Strictly two people are aboard: the female captain in her rust-orange jacket and dark red life vest steering at the helm, and one male crewmate sitting beside stacked supply crates on the rear deck. They steer past the tilted rusted wreck of a half-sunken ship resting silently on the misty rocks to the right. As the boat clears the silent wreck, the silver sea fog parts ahead to reveal three separate rugged green highland islands emerging across open channels in soft morning light. Steady boat weight, no cuts, no readable text.
  ```

---

### S06｜00:50–01:00（10s）：发现三岛群岛与暗毁灯塔 —— 《潮线之上》标题落版

* **画面目的**：完全对齐实机地图——**主岛 + 西副岛 + 东副岛（共三座分离岛屿）**、**东岛搁浅沉船**、以及礁石上**被陨石撞毁且完全熄灭的暗色灯塔废墟底座（Stage 0 废墟，绝非完整亮灯高塔）**；无沙滩、只有岩石避风湾，镜头拉升至实机 45° 俯瞰并留白出标题。
* **首帧 `S06_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S06_A in the exact same theatrical 2D anime film style.
  Scene: Medium aerial view looking slightly down behind the exact same orange-and-white rescue boat (carrying STRICTLY TWO PEOPLE ONLY: one woman at the helm + one man on the stern deck) as it glides toward a sheltered dark rocky stone landing cove (NO sandy beach) at the base of the rugged, uninhabited Main Island (layered gray basalt rock terraces, green grassy plains, coastal pines and broadleaf trees, small mountain stream and central pond). Across open deep-teal water channels in the background, two smaller satellite islands (West Island on left, East Island on right) are visible, plus a small detached sea reef bearing the dark, unlit, meteor-shattered low circular stone foundation stump of a destroyed lighthouse (NO tall tower, NO lantern, completely dark broken ruin). Soft golden sunrise rays illuminate the island ridges. Untouched natural terrain, NO buildings yet, NO UI, NO text, 16:9.
  ```
* **尾帧 `S06_B`（同对话续画指令）**：
  ```text
  Generate S06_B by craning the camera high and back into a grand elevated 45-degree overview matching the real three-island archipelago layout in S06_A and the 2D anime film style.
  Three distinct separate green-and-rocky islands sit in a triangle across the deep-teal sea:
  1) Largest Main Island in the lower-center foreground (rocky ledges, green highland terraces, scattered pine and broadleaf trees, small mountain stream feeding a central pond, and the tiny orange-and-white rescue boat moored quietly in a rocky cove with NO sandy beach);
  2) Smaller elongated West Satellite Island across an open sea channel in the upper-left midground;
  3) Smaller East Satellite Island across an open sea channel in the upper-right midground with the tilted rusted red capsized shipwreck resting on its western rocky shore;
  4) On a small detached rocky reef islet near the eastern channel sits ONLY the dark, completely unlit, meteor-shattered low broken stone stump of the ruined lighthouse (NO intact tall tower, NO glowing light).
  Soft golden morning sunbeams break through clouds onto the islands while generous calm open misty ocean and sky fill the upper-left corner as clean negative space for a game title overlay. Quiet enduring hope, NO buildings, NO UI, NO text, 16:9.
  ```
* **Flow 视频提示词（`S06_A → S06_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, sweeping tranquil establishing shot in deep teal ocean tones bathed in soft golden sunrise rays. One continuous 10-second smooth aerial crane pull-up and slow slight orbit rising above the small orange-and-white rescue boat (carrying two rescuers) as it glides gently into the sheltered rocky cove and comes to rest. As the camera climbs into a wide high-angle overview, it reveals the entire three-island archipelago separated by deep teal channels: the large terraced green Main Island with its stream and pond below, the elongated West Island to the upper left, the East Island with its beached rusted shipwreck to the upper right, and a small detached sea reef holding only the dark, unlit, shattered stone stump of a destroyed lighthouse. The final 2 seconds settle into a rock-steady scenic frame with generous calm misty sky negative space in the upper left for a title card. Smooth eased finish, no popping buildings, no text.
  ```

---

## 后期字幕精简方案（共 5 句，刚好压住 60 秒节奏）

* **S01（00:00–00:10）**：*“起初，我们成功拦截了第一批碎冰——所有人都以为危机已经过去。”*
* **S02（00:10–00:20）**：*“没有人察觉，太阳眩光背后正拖着整片崩解的冰核主云。”*
* **S03（00:20–00:30）**：*“防线来不及反应。海啸倾覆了海岸，电网与卫星相继沉寂。”*
* **S04（00:30–00:40）**：*“冰水仍在不定期坠落，潮线年复一年攀升。高台上的短波，成了幸存者最后的联系。”*
* **S05–S06（00:40–01:00）**：*“顺着微弱的求救信号，我们驶过沉船，找到了这片仍在潮线之上的高地。”*
