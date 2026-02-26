# YouTube Cookies 文件

## 如何获取 YouTube Cookies

由于 YouTube 需要登录验证，你需要先导出 cookies.txt 文件。

### 方法 1: 使用浏览器插件 (推荐)

1. **安装浏览器插件**（Chrome/Edge 都可以）：
   - 搜索：**"Get cookies.txt LOCA"**
   - 或搜索：**"cookies.txt"**

2. **登录 YouTube**：
   - 打开 https://www.youtube.com
   - 确保已登录

3. **导出 cookies**：
   - 点击浏览器右上角的插件图标
   - 选择 "Current site"
   - 点击 "Export" 或 "Download"
   - 保存为 `cookies.txt`

4. **放置文件**：
   - 将 `cookies.txt` 放到这个目录：
   ```
   C:\AI-Agent-Local\.claude\skill\video-transcribe\cookies.txt
   ```

### 方法 2: 使用在线工具

1. 访问：https://getcookies.net/
2. 按网站说明操作
3. 下载 cookies.txt
4. 放到上述目录

## 注意事项

- cookies 文件包含敏感信息，请妥善保管
- cookies 可能会过期，如果遇到问题重新导出
- 不要分享你的 cookies.txt 文件

## 验证

完成上述步骤后，重新运行程序即可。

```bash
cd C:\AI-Agent-Local\.claude\skill\video-transcribe\scripts
python main.py <YouTube视频链接>
```
