"""直接向数据库插入/更新视觉预设模板的脚本。"""
import json
import uuid
import psycopg2

CONN = "dbname=shortfilm user=shortfilm password=shortfilm123 host=localhost port=5432"

UPDATED = {
    "古风仙侠": json.dumps({
        "art_style": "中国水墨画风，空灵飘逸",
        "era": "ancient",
        "environment": "浮空仙岛，竹林，瀑布，天宫",
        "lighting": "柔和月光，灵气光芒，金色光尘",
        "color_palette": "翡翠绿，淡金，墨黑，云白",
        "camera_angle": "远景，优雅构图",
        "render_quality": "精细水墨渲染，4K，电影级，传统国画质感",
        "global_note": "所有角色统一古风仙侠美学，飘逸长袍，灵气光环",
    }, ensure_ascii=False),
    "都市甜宠": json.dumps({
        "art_style": "动漫风格，柔和渲染",
        "era": "modern",
        "environment": "豪华公寓，现代办公室，樱花公园，咖啡厅",
        "lighting": "暖色柔光，黄金时段，自然阳光",
        "color_palette": "粉色，暖白，柔金色",
        "camera_angle": "中景，微俯拍",
        "render_quality": "精细，4K，电影级",
        "global_note": "柔和浪漫氛围，所有角色保持统一的暖色调光影",
    }, ensure_ascii=False),
    "赛博朋克": json.dumps({
        "art_style": "半写实，赛博朋克美学",
        "era": "near_future",
        "environment": "霓虹灯小巷，雨夜街道，全息广告牌，地下俱乐部",
        "lighting": "霓虹辉光，蓝紫色轮廓光，体积雾",
        "color_palette": "霓虹蓝，品红，青色，深紫",
        "camera_angle": "低角度，戏剧性透视",
        "render_quality": "虚幻引擎5，8K，光线追踪，电影级",
        "global_note": "高对比霓虹光影，雨水与反射，统一赛博朋克氛围",
    }, ensure_ascii=False),
    "末世废土": json.dumps({
        "art_style": "粗粝写实，末世风格",
        "era": "post_apocalyptic",
        "environment": "废墟城市，废弃工厂，沙漠荒原，地下避难所",
        "lighting": "烈日强光，尘雾弥漫，闪烁日光灯",
        "color_palette": "低饱和橙，锈褐，灰烬灰，暗绿",
        "camera_angle": "远景建立镜头，纪实风格",
        "render_quality": "照片级写实，4K，胶片颗粒感，电影级",
        "global_note": "破旧沧桑质感，所有角色展现生存磨损，统一废土氛围",
    }, ensure_ascii=False),
    "暗黑玄幻": json.dumps({
        "art_style": "暗黑奇幻，精细插画",
        "era": "fantasy",
        "environment": "哥特城堡，暗黑森林，地下王座，血月天空",
        "lighting": "明暗对比布光，火光，不祥辉光",
        "color_palette": "深红，漆黑，暗紫，银色",
        "camera_angle": "戏剧性低角度，倾斜构图",
        "render_quality": "超精细，4K，电影级，压抑氛围",
        "global_note": "暗黑戏剧性基调，所有角色统一哥特奇幻设定",
    }, ensure_ascii=False),
}

NEW_PRESETS = [
    ("校园青春", "清新明亮的校园风格，适合校园/青春/恋爱题材", {
        "art_style": "动漫风格，线条干净，明亮色彩",
        "era": "modern",
        "environment": "校园，教室，天台，图书馆，运动场",
        "lighting": "明亮自然光，镜头光晕，柔和阴影",
        "color_palette": "天蓝，草绿，校服白，樱花粉",
        "camera_angle": "平视，柔和构图",
        "render_quality": "干净动漫风，4K，鲜艳色彩",
        "global_note": "明亮青春氛围，所有角色统一校园场景风格",
    }),
    ("蒸汽朋克", "齿轮与蒸汽的机械美学，适合蒸汽朋克/机械/冒险题材", {
        "art_style": "蒸汽朋克插画，精细机械风",
        "era": "victorian_futurism",
        "environment": "钟表工坊，飞艇甲板，黄铜塔楼，齿轮城市",
        "lighting": "暖色钨丝灯，蒸汽逆光，琥珀色辉光",
        "color_palette": "黄铜金，铜色，红木棕，青蓝点缀",
        "camera_angle": "对称构图，机械框架",
        "render_quality": "精密细节，4K，电影级，金属质感",
        "global_note": "维多利亚机械美学，所有角色穿着蒸汽朋克时代服饰",
    }),
    ("黑色悬疑", "经典黑色影调的悬疑风格，适合悬疑/推理/犯罪题材", {
        "art_style": "黑色电影风格，高对比",
        "era": "mid_century",
        "environment": "雨夜街道，昏暗办公室，烟雾缭绕的酒吧，阴暗小巷",
        "lighting": "百叶窗阴影，台灯单光源，烟雾弥漫",
        "color_palette": "黑色，白色，银色，暗暖色调",
        "camera_angle": "倾斜角度，特写，戏剧性阴影",
        "render_quality": "胶片颗粒感，4K，黑色电影摄影",
        "global_note": "高对比黑白美学，所有角色统一阴影与悬疑氛围",
    }),
    ("悬疑惊悚", "黑暗恐怖的惊悚风格，适合悬疑/惊悚/恐怖题材", {
        "art_style": "黑暗写实，高对比",
        "era": "modern",
        "environment": "废弃医院，雨夜小巷，密室，地下通道",
        "lighting": "闪烁冷光灯，阴影遮挡，底光照明",
        "color_palette": "黑色，灰色，暗红，深紫",
        "camera_angle": "特写，低角度，荷兰角倾斜",
        "render_quality": "4K，电影噪点，暗角效果",
        "global_note": "压抑恐怖氛围，所有角色表情紧张，统一阴暗冷色调",
    }),
    ("科幻机甲", "硬核科幻机甲风格，适合机甲/太空战/硬科幻题材", {
        "art_style": "硬科幻，机械质感，工业设计风",
        "era": "far_future",
        "environment": "太空战舰，机甲工厂，行星基地，星际港口",
        "lighting": "蓝色冷光，金属反光，全息投影光",
        "color_palette": "银色，科技蓝，黑色，橙色点缀",
        "camera_angle": "全景，推镜，仰视巨物感",
        "render_quality": "虚幻引擎5，8K，光线追踪，金属质感",
        "global_note": "硬核机械美学，所有角色统一科幻工业风格，机甲细节丰富",
    }),
    ("童话奇幻", "明亮梦幻的童话风格，适合童话/奇幻/儿童题材", {
        "art_style": "绘本风格，水彩质感，柔和线条",
        "era": "fantasy",
        "environment": "魔法森林，糖果屋，精灵树屋，彩虹桥",
        "lighting": "柔和魔法光，梦幻散射，星光点缀",
        "color_palette": "粉色，紫色，金色，薄荷绿",
        "camera_angle": "中景，微俯视，温暖构图",
        "render_quality": "4K，水彩渲染质感，柔和色彩过渡",
        "global_note": "梦幻童话氛围，所有角色造型可爱，统一明快色调",
    }),
    ("神话史诗", "庄严宏大的神话风格，适合神话/史诗/传奇题材", {
        "art_style": "油画风格，庄严厚重",
        "era": "mythology",
        "environment": "奥林匹斯山，天宫，巨人之地，神殿",
        "lighting": "神圣金光，自然光，天堂射线",
        "color_palette": "金色，白色，宝蓝，深红",
        "camera_angle": "全景，仰拍，史诗构图",
        "render_quality": "8K，电影级，油画质感渲染",
        "global_note": "庄严神圣氛围，所有角色服装华丽，统一史诗气势",
    }),
    ("黑帮犯罪", "黑色电影风格的犯罪题材，适合黑帮/犯罪/警匪题材", {
        "art_style": "黑色电影风格，半写实",
        "era": "1920s",
        "environment": "街头，酒吧，豪华办公室，地下赌场",
        "lighting": "低调光，百叶窗阴影，烟雾氛围",
        "color_palette": "黑色，灰色，酒红，暗金",
        "camera_angle": "中景，低角度，阴影构图",
        "render_quality": "4K，胶片颗粒，复古色调",
        "global_note": "复古犯罪美学，所有角色穿着西装或皮衣，统一暗色调",
    }),
    ("医疗职场", "明亮写实的医疗风格，适合医疗/职场/都市题材", {
        "art_style": "写实风格，明亮干净",
        "era": "modern",
        "environment": "医院走廊，手术室，病房，医生办公室",
        "lighting": "白色日光灯，无影灯，自然窗光",
        "color_palette": "白色，浅蓝，薄荷绿，肤色",
        "camera_angle": "中景，平视，纪实构图",
        "render_quality": "4K，清晰锐利，自然色彩",
        "global_note": "专业医疗氛围，所有角色穿着白大褂或护士服，统一明亮干净风格",
    }),
    ("体育竞技", "动感热血的体育风格，适合体育/竞技/热血题材", {
        "art_style": "半写实，动感线条，高饱和",
        "era": "modern",
        "environment": "体育场，训练馆，游泳池，赛道",
        "lighting": "聚光灯，自然光，汗水反光",
        "color_palette": "红色，蓝色，白色，活力黄",
        "camera_angle": "中景，跟拍，动态角度",
        "render_quality": "4K，运动模糊效果，高帧率感",
        "global_note": "热血动感氛围，所有角色体态健壮，统一明亮高饱和风格",
    }),
    ("历史战争", "厚重写实的历史战争风格，适合战争/历史/军事题材", {
        "art_style": "写实风格，厚重质感",
        "era": "historical",
        "environment": "战壕，城墙，古战场，军营",
        "lighting": "硝烟弥漫，火光，黄昏光",
        "color_palette": "军绿，褐色，灰色，血红点缀",
        "camera_angle": "远景，摇移镜头，俯拍战场",
        "render_quality": "4K，纪实风格，胶片质感",
        "global_note": "战争沧桑氛围，所有角色着军装或古代战甲，统一厚重写实风格",
    }),
    ("末日生存", "阴郁紧张的末日生存风格，适合末世/丧尸/求生题材", {
        "art_style": "写实，阴郁，压抑色调",
        "era": "near_future",
        "environment": "废弃城市，避难所，荒野，地下通道",
        "lighting": "阴天散射光，手电筒聚光，闪烁应急灯",
        "color_palette": "灰色，暗绿，黑色，铁锈红",
        "camera_angle": "中景，手持跟拍，晃动感",
        "render_quality": "4K，手持抖动感，低饱和",
        "global_note": "紧张生存氛围，所有角色衣衫褴褛，统一阴郁压抑风格",
    }),
    ("星际探险", "宏大壮美的星际探险风格，适合太空/星际/科幻冒险题材", {
        "art_style": "科幻，宏大壮美，精细渲染",
        "era": "far_future",
        "environment": "外星地表，宇宙飞船，空间站，虫洞",
        "lighting": "星光，高科技蓝色光效，异星日光",
        "color_palette": "深空蓝，星紫，银白，能量橙",
        "camera_angle": "远景广角，太空纵深感",
        "render_quality": "8K，太空感渲染，星云特效",
        "global_note": "宏大太空美学，所有角色穿太空服，统一星际探险风格",
    }),
]


def main():
    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    # 1. 更新已有预设为中文
    for name, settings_json in UPDATED.items():
        cur.execute(
            "UPDATE visual_templates SET settings = %s WHERE name = %s",
            (settings_json, name),
        )
        print(f"  更新: {name}")

    # 2. 获取已有名称
    cur.execute("SELECT name FROM visual_templates")
    existing = {row[0] for row in cur.fetchall()}

    # 3. 插入新预设
    inserted = 0
    for name, desc, settings in NEW_PRESETS:
        if name not in existing:
            cur.execute(
                "INSERT INTO visual_templates (id, name, description, settings, is_system) VALUES (%s, %s, %s, %s, true)",
                (str(uuid.uuid4()), name, desc, json.dumps(settings, ensure_ascii=False)),
            )
            inserted += 1
            print(f"  新增: {name}")
        else:
            print(f"  跳过（已存在）: {name}")

    conn.commit()

    # 4. 验证
    cur.execute("SELECT name FROM visual_templates WHERE is_system = true ORDER BY name")
    all_templates = [row[0] for row in cur.fetchall()]
    print(f"\n完成！共 {len(all_templates)} 个系统预设:")
    for t in all_templates:
        print(f"  - {t}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
