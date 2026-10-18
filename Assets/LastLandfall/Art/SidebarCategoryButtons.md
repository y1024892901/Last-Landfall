# 左侧功能栏目图片

图片：`Resources/UI/Sidebar/CategoryButtonsAtlas.png`。
渲染：`Scripts/SidebarCategoryArtwork.cs`。

按已确认的深青色与黄铜边框预览制作，使用内置 image_gen 提取三个普通状态按钮。原始生成文件保留不变，完整图集复制进项目，通过 UV 选取三个按钮，避免重复生成时丢失画面。图集原尺寸 1024×1536，禁用非二次幂缩放、压缩和 mipmap。

当前仅通过 UV 读取图案区域：科技 (346,164,324,236)、文化 (362,613,300,211)、建筑 (366,1028,290,238)。原图中的厚金属外框和文字不再显示。按钮为 64×64，间距 8；细切角边框、暗色渐变底板、悬停和选中状态均由代码绘制，标签使用实时简体中文。常态边框低对比，选中时显示单层暖金边线，侧栏底板不叠加外框。

## 最终生成提示词

> Asset extraction for production Unity UI. Extract and reproduce ONLY the THREE LEFT SIDEBAR SQUARE BUTTONS from this approved screenshot, as one vertical three-cell sprite atlas on a genuinely transparent canvas. Preserve the approved appearance: fine beveled aged brass clipped-corner frames, recessed dark teal centers, gold shallow relief symbols, Chinese labels integrated below. TOP '科技' with brass microchip and tiny cyan traces; MIDDLE '文化' with open gold parchment book; BOTTOM '建筑' with roof, crossed hammer and ruler. Each button SAME square size and same brass frame geometry, evenly stacked vertically with equal small TRANSPARENT gaps, 4 percent transparent padding around entire sheet. ALL THREE in matching normal unselected state: no neon glow on the building button, same restrained brass rim brightness as technology and culture. Buttons fully opaque inside their frame. Remove all surrounding UI, the top resource header, adjacent construction panel, ocean, background, and large outer sidebar rail. No extra buttons, no other text, no drop shadow extending outside the square. Preserve approved symbols, palette and wording, do not redesign. The result is a clean reusable game UI atlas, 1 column by 3 rows, complete visible button edges, camera perfectly front on, zero perspective, transparent outside buttons. This will render at about 52px per button, so keep symbols crisp and centered.
