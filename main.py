import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import yt_dlp


DRIVER_PATH = r"\chromedriver.exe" #chromedriver路径

def scrape_youtube(url,scroll_pause_time=2, max_scrolls=10):
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    # 打开 YouTube 频道
    driver.get(url)
    time.sleep(5)
    # 获取视频标题和链接
    scroll_count = 0
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:  # 没有新的内容加载
            break
        last_height = new_height
        scroll_count += 1
    videos = driver.find_elements(By.XPATH, '//*[@id="video-title-link"]')
    linklist = []
    for video in videos:
        title = video.get_attribute("title")
        link = video.get_attribute("href")
        if title and link:
            linklist.append({"title": title, "url": link})
        print(f"Title: {title}, Link: {link}")
    driver.quit()
    return linklist

def writetofile(filepath,videoName,videoUrl):
    with open(f"{filepath}", "a", encoding="utf-8") as f:
        f.write(f"Title: {videoName}\n")
        f.write(f"URL: {videoUrl}\n")
        f.write("-" * 50 + "\n")
def download_video_with_audio_yt_dlp(video_url, save_path="downloads"):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",  # 下载最佳视频流和最佳音频流并合并
        "merge_output_format": "mp4",         # 合并后的格式
        "outtmpl": f"{save_path}/%(title)s.%(ext)s",  # 输出路径和文件名
        "cookiefile": 'cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def read_videos_from_file(file_path):
    videos = []
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    video = {}
    for line in lines:
        line = line.strip()  # 去除两端的空格和换行符
        if line.startswith("Title:"):
            # 提取视频标题
            video["title"] = line.replace("Title:", "").strip()
        elif line.startswith("URL:"):
            # 提取视频 URL
            video["url"] = line.replace("URL:", "").strip()
        elif line.startswith("-" * 50):
            # 如果遇到分隔符，表示视频记录结束
            if video:
                videos.append(video)
                video = {}
    return videos
if __name__ == "__main__":
    url = '待添加的URL'
    lklist = scrape_youtube(url)
    time.sleep(random.randint(1, 10))
    #载入已下载列表，避免重复下载
    recordedURLList = []
    if os.path.isfile('DownLoadedVideoList.txt'):
        recordedVideoList = read_videos_from_file('DownLoadedVideoList.txt')
        for item in recordedVideoList:
            recordedURLList.append(item['url'])
    #下载循环
    i = 1
    for video in lklist:
        retry_count = 0
        max_retries = 3  # 最大重试次数
        #遇到传输错误时重新执行，重传次数不超过3
        while retry_count < max_retries:
            try:
                if video['url'] not in recordedURLList:
                    print(f'下载进度: 正在下载第{i}个视频: {video["title"]}')
                    download_video_with_audio_yt_dlp(video["url"])
                    writetofile("DownLoadedVideoList.txt", video["title"], video["url"])
                    recordedURLList.append(video['url'])
                    print(video['url'])
                    i = i + 1
                break  # 如果成功，退出内层循环
            except yt_dlp.utils.DownloadError as e:
                retry_count += 1
                print(f"下载 {video['title']} 时出错: {e}")
                print(f"正在重试 ({retry_count}/{max_retries})...")
                if retry_count == max_retries:
                    print(f"跳过视频 {video['title']}，重试次数已达上限。")
