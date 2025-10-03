# V 3.0
"""
zh-CN  --  Chinese  -- 简体中文
功能介绍:
本程序用于代理管理,有以下几个功能:
1.爬取和验证新代理,并将通过的代理添加到代理池文件(OUTPUT_FILE).为了使每个代理得到充分使用,本程序采取新代理验证两遍的策略,只要有一次通过即算通过,确保不会落下任何一个可用代理.
    在验证之前会先将重复代理,错误代理筛除,确保不做无用功.满分100分,有效代理验证成功默认分数98分,超时代理80分,错误代理和无效代理0分(会被0分清除函数清除).
2.检验和更新代理池内代理的有效性,再次验证成功加1分,超时代理分不变,无效代理和错误代理减1分,更直观的分辨代理的稳定性.
3.提取指定数量的代理,优先提取分数高,稳定的代理
4.查看代理池状态(总代理数量,代理的分数分布情况)
5.从csv文件(ip,port格式)加载并验证代理,用于手动添加代理时使用

代理池文件格式(OUTPUT_FILE) -> csv
Proxy,Port,Score
代理,端口,分数

建议将此程序放到proxies文件夹下,如果想放到其他地方,请修改'OUTPUT_FILE = "../proxies/valid_proxies.csv"'中的proxies为你的文件夹名称


en  -- English  --  英语
Function Introduction:
This program is used for proxy management and has the following functions:
1. Crawl and verify new proxies, and add the verified proxies to the proxy pool file (OUTPUT_FILE).To ensure each proxy is fully utilized, 
    this program adopts a strategy of verifying new proxies twice; as long as one verification passes, it is considered successful, ensuring that no usable proxy is missed.
    Before verification, duplicate and erroneous proxies are filtered out to avoid unnecessary work. 
    The full score is 100 points.Successfully verified valid proxies are given a default score of 98, timed-out proxies 80, 
    and erroneous or invalid proxies 0 (which will be removed by the zero-score cleanup function).
2. Check and update the validity of proxies in the proxy pool. Successfully re-verified proxies gain 1 point, timed-out proxies retain their score,
    and invalid or erroneous proxies lose 1 point, which helps to intuitively assess proxy stability.
3. Extract a specified number of proxies, prioritizing high-score and stable proxies.
4. View the status of the proxy pool (total number of proxies, score distribution).
5. Load and verify proxies from a CSV file (in IP, port format), useful for manually adding proxies.

Proxy pool file format (OUTPUT_FILE) -> CSV
Proxy,Port,Score
It is recommended to place this program in the 'proxies' folder. 
If you want to place it elsewhere, please modify 'OUTPUT_FILE = "../proxies/valid_proxies.csv"' by changing 'proxies' to your folder name.
"""
import re
import requests
import concurrent.futures
import time
import os
import sys
import csv
import socket

# ============默认配置区 - Default Configuration
OUTPUT_FILE = "../proxies/valid_proxies.csv"  # 输出有效代理文件（CSV格式）- Export valid proxy file (CSV format)
TEST_URL = "http://httpbin.org/ip"  # 测试使用的URL - URL used for testing
TIMEOUT = 6  # 超时时间(秒) - Timeout (s)
MAX_WORKERS = 20  # 最大并发数 - Maximum concurrency
MAX_SCORE = 100  # 最大积分 - Maximum score

# 设置全局超时（包括DNS解析）
socket.setdefaulttimeout(TIMEOUT)

class ProxyScraper:
    """
    get ip

    :param url: 请求地址
    :param regex_pattern: re解析式，用于解析爬取结果
    :param capture_groups: 要返回的re中的值，[IpName,Port]
    :return: [proxy:port]
    """

    def __init__(self, url: str, regex_pattern: str, capture_groups: list):
        self.url = url
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0'
        }
        self.encoding = "utf-8"
        self.regex_pattern = regex_pattern
        self.capture_groups = capture_groups

    def scrape_proxies(self):
        extracted_data = []
        try:
            response = requests.get(url=self.url, headers=self.headers, timeout=TIMEOUT)
            if response.status_code == 200:  # 判断状态码
                response.encoding = self.encoding  # 使用utf-8
                regex = re.compile(self.regex_pattern, re.S)  # 创建一个re对象
                matches = regex.finditer(response.text)  # 对获取的东西进行解析
                for match in matches:
                    for group_name in self.capture_groups:  # 依次输出参数capture_groups中的指定内容
                        extracted_data.append(f"{match.group(group_name)}")
                proxy_list = [f"{extracted_data[i].strip()}:{extracted_data[i + 1].strip()}" for i in
                            range(0, len(extracted_data), 2)]  # 整合列表为[proxy:port]
                response.close()
                return proxy_list
            else:
                get_error = f"爬取失败，❌ 状态码{response.status_code}"
                print(get_error)
                return get_error

        except Exception as e:
            get_error = f"爬取失败，❌ 错误: {str(e)}"
            print(get_error)
            return get_error

def check_proxy(proxy, test_url="http://httpbin.org/ip", timeout=TIMEOUT, retries=1):
    """
    检查单个代理IP的可用性（支持重试）

    :param proxy: 代理IP地址和端口 (格式: ip:port)
    :param test_url: 用于测试的URL
    :param timeout: 请求超时时间(秒)
    :param retries: 重试次数
    :return: (代理地址, 是否可用, 响应时间)
    """
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }

    for attempt in range(retries):
        try:
            start_time = time.time()
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=timeout,
                allow_redirects=False  # 禁止重定向
            )
            end_time = time.time()
            response_time = end_time - start_time

            # 检查响应时间是否超过超时限制
            if response_time > timeout:
                return proxy, False, response_time

            # 检查响应状态码和内容有效性
            if response.status_code == 200:
                # 验证返回的IP是否与代理一致（可选）
                origin_ip = response.json().get('origin', '')
                if proxy.split(':')[0] in origin_ip:
                    return proxy, True, response_time
                return proxy, True, response_time
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.JSONDecodeError,
                requests.exceptions.TooManyRedirects):
            if attempt < retries - 1:
                time.sleep(0.5)  # 短暂等待后重试
                continue
            return proxy, False, None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
            return proxy, False, None
    return proxy, False, None

def check_proxies_batch(proxies, test_url="http://httpbin.org/ip", timeout=TIMEOUT, max_workers=MAX_WORKERS, check_type="existing"):
    """
    批量检查代理IP列表

    :param proxies: 代理IP列表或字典
    :param test_url: 测试URL
    :param timeout: 超时时间(秒)
    :param max_workers: 最大线程数
    :param check_type: "new"（新代理）或 "existing"（已有代理）
    :return: 更新后的代理字典
    """
    updated_proxies = {}

    # 如果是新代理，使用两次重试
    retries = 2 if check_type == "new" else 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {
            executor.submit(
                check_proxy,
                proxy,
                test_url,
                timeout,
                retries
            ): proxy for proxy in proxies
        }

        for future in concurrent.futures.as_completed(future_to_proxy):
            try:
                proxy, is_valid, response_time = future.result()

                # 验证成功
                if is_valid and response_time is not None and response_time <= timeout:
                    print(f"✅ 有效代理: {proxy} | 响应时间: {response_time:.2f}s")
                    if check_type == "new":
                        # 新代理验证成功给98分（而不是满分）
                        updated_proxies[proxy] = 98
                    else:
                        # 已有代理验证成功加1分（不超过最大分）
                        current_score = proxies.get(proxy, 0)
                        updated_proxies[proxy] = min(current_score + 1, MAX_SCORE)
                    
                # 响应结果超过规定的'timeout',但至少不是None
                elif response_time is not None:
                    print(f"❎ 超时代理: {proxy} | 响应时间: {response_time:.2f}s")
                    if check_type == "existing" and proxy in proxies:
                        # 已有代理验证超时不改分
                        updated_proxies[proxy] = proxies[proxy]
                    else:
                        # 新代理验证超时给80分
                        updated_proxies[proxy] = 80

                # 响应结果为'None'时
                else:
                    print(f"❌ 无效代理: {proxy} | 响应结果: {response_time}")
                    if check_type == "existing" and proxy in proxies:
                        # 已有代理验证无效减1分（不低于0分）
                        updated_proxies[proxy] = max(0, proxies[proxy] - 1)
                    else:
                        # 新代理验证无效给0分
                        updated_proxies[proxy] = 0 
            except Exception as e:   # 一般在爬取部分就筛选完了,这是为了保险起见
                print(f"❌ 错误代理: {proxy}")   
                if check_type == "existing" and proxy in proxies:
                    # 已有代理验证错误减1分（不低于0分）
                    updated_proxies[proxy] = max(0, proxies[proxy] - 1)
                else:
                    # 新代理验证错误给0分
                    updated_proxies[proxy] = 0  
    return updated_proxies

def load_proxies_from_file(file_path):
    """从CSV文件加载代理列表和分数"""
    proxies = {}
    if not os.path.exists(file_path):
        return proxies

    with open(file_path, 'r', encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2:
                proxy = row[0].strip()
                try:
                    score = int(row[1])
                    proxies[proxy] = score
                except:
                    # 如果分数解析失败，使用默认值
                    proxies[proxy] = 70
    return proxies

def save_valid_proxies(proxies, file_path):
    """保存有效代理到CSV文件（带分数）"""
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        for proxy, score in proxies.items():
            if len(f'{proxy}:{score}') > 6:   # 去掉错误的长度不够的代理
                if score > 0:  # 只保存分数大于0的代理
                    writer.writerow([proxy, score])

def update_proxy_scores(file_path):
    """更新代理分数文件，移除0分代理"""
    proxies = load_proxies_from_file(file_path)
    valid_proxies = {k: v for k, v in proxies.items() if v > 0}
    save_valid_proxies(valid_proxies, file_path)
    return len(proxies) - len(valid_proxies)

def extract_proxies(num):
    """
    提取指定数量的代理，优先提取分高的

    :param num: 要提取的代理数量
    :return: 代理列表
    """
    proxies = load_proxies_from_file(OUTPUT_FILE)

    # 按分数降序排序
    sorted_proxies = sorted(proxies.items(), key=lambda x: x[1], reverse=True)

    # 提取代理
    result = []
    for proxy, score in sorted_proxies:
        if len(result) >= num:
            break
        result.append(proxy)

    return result

def filter_proxies(all_proxies):
        """
        从新获取代理中去掉无效的,重复的
        :all_proxies: 新代理列表
        :return: 筛选后的代理列表
        """
        # 进行筛选
        existing_proxies = []
        with open(OUTPUT_FILE,'r') as file:
            csv_reader  = csv.reader(file)
            for row in csv_reader:
                existing_proxies.append(row[0])

        new_proxies = []
        duplicate_count = 0
        invalid_count = 0

        for proxy in all_proxies:
            try:
                if proxy in existing_proxies:
                    print(f'⭕️ 已有代理: {proxy}')
                    duplicate_count += 1
                elif ':' in proxy:
                    new_proxies.append(proxy)
                else:
                    print(f'❌ 格式无效: {proxy}')
                    invalid_count += 1
            except:
                invalid_count += 1

        print(f'新代理:{len(new_proxies)},已有(重复):{duplicate_count},无效:{invalid_count}')
        return new_proxies

def validate_new_proxies(new_proxies):
    """验证新代理"""
    if not new_proxies:
        print("没有代理需要验证")
        return

    print(f"共加载 {len(new_proxies)} 个新代理，开始测试...")
    updated_proxies = check_proxies_batch(new_proxies, TEST_URL, TIMEOUT, MAX_WORKERS, check_type="new")

    # 保留所有验证结果（包括98分和80分的代理）
    # valid_new_proxies = {k: v for k, v in updated_proxies.items() if v == 98}  # 原代码，只保留98分
    valid_new_proxies = updated_proxies  # 修改后，保留所有分数

    # 合并到现有代理池
    existing_proxies = load_proxies_from_file(OUTPUT_FILE)
    for proxy, score in valid_new_proxies.items():
        # 只添加新代理或更新分数（取最高分）
        if proxy not in existing_proxies or existing_proxies[proxy] < score:
            existing_proxies[proxy] = score

    save_valid_proxies(existing_proxies, OUTPUT_FILE)

    # 统计验证结果
    success_count = sum(1 for score in valid_new_proxies.values() if score == 98)

    timeout_count = sum(1 for score in valid_new_proxies.values() if score == 80)

    print('\n验证完成!' )
    print(f"新代理成功: {success_count}/{len(new_proxies)}")
    print(f"新代理超时：{timeout_count}/{len(new_proxies)}")

    print(f"代理池已更新至: {OUTPUT_FILE}")

def validate_existing_proxies():
    """验证已有代理池中的代理"""
    print(f"开始验证已有代理池，文件：{OUTPUT_FILE}...")

    proxies = load_proxies_from_file(OUTPUT_FILE)

    # 记录验证前的代理数量
    initial_count = len(proxies)

    if not proxies:
        print("代理池为空，请先添加代理")
        return

    print(f"共加载 {len(proxies)} 个代理，开始测试...")
    updated_proxies = check_proxies_batch(proxies, TEST_URL, TIMEOUT, MAX_WORKERS, "existing")

    # 保存更新后的代理池
    save_valid_proxies(updated_proxies, OUTPUT_FILE)

    # 清理0分代理
    removed_count = update_proxy_scores(OUTPUT_FILE)

    # 记录验证后的代理数量
    final_count = len(load_proxies_from_file(OUTPUT_FILE))

    print(f"\n验证完成! 剩余有效代理: {final_count}/{initial_count}")
    print(f"代理分数已更新，已移除 {initial_count - final_count} 个无效代理")

def crawl_proxies():
    """爬取免费代理 - 仅供学习参考"""
    print("""已创建的可爬网站
    1：https://proxy5.net/cn/free-proxy/china   -被封了,但代理质量很高
    2：https://www.89ip.cn/   -240个,但大多数不能用
    3：https://cn.freevpnnode.com/   -30个,但大多数不能用
    4：https://www.kuaidaili.com/free/inha/   -7600多页,一页12个,总体质量不高,但有部分可以用
    5：http://www.ip3366.net/   -100个,但大多数不能用
    6：https://proxypool.scrape.center/random   -随机的,整体质量较高
    7：https://proxy.scdn.io/text.php   -12000多个,1/3可以用
    8：https://proxyhub.me/zh/cn-http-proxy-list.html   -20个,都不能用
          
    输入其他：退出
    """)
    scraper_choice = input("选择：")
    all_proxies = []  # 存储所有爬取的代理

    if scraper_choice == "1":
        print('开始爬取:https://proxy5.net/cn/free-proxy/china')
        error_count = 0
        '''
        <tr>.*?<td><strong>(?P<ip>.*?)</strong></td>.*?<td>(?P<port>.*?)</td>.*?</tr>
        '''
        proxy_list = ProxyScraper('https://proxy5.net/cn/free-proxy/china',
                        "<tr>.*?<td><strong>(?P<ip>.*?)</strong></td>.*?<td>(?P<port>.*?)</td>.*?</tr>",
                        ["ip", "port"]).scrape_proxies()
        
        if isinstance(proxy_list, list):
            all_proxies.extend(proxy_list)
        else:
            error_count += 1
        print(f'100%|██████████████████████████████████████████████████| 1/1  错误数:{error_count}')
    elif scraper_choice == "2":
        print('开始爬取:https://www.89ip.cn/')
        error_count = 0
        total_pages = 6
        for page in range(1, total_pages+1):
            if page == 1:
                url = 'https://www.89ip.cn/'
            else:
                url = f'https://www.89ip.cn/index_{page}.html'

            proxy_list = ProxyScraper(url,"<tr>.*?<td>(?P<ip>.*?)</td>.*?<td>(?P<port>.*?)</td>.*?</tr>",
                            ["ip", "port"]).scrape_proxies()
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1

            time.sleep(1)

            # 计算进度百分比
            percent = page * 100 // total_pages
            # 计算进度条长度
            completed = page * 50 // total_pages
            remaining = 50 - completed
            # 处理百分比显示的对齐
            if percent < 10:
                padding = "  "
            elif percent < 100:
                padding = " "
            else:
                padding = ""
            # 更新进度条
            print(f"\r{percent}%{padding}|{'█' * completed}{'-' * remaining}| {page}/{total_pages}  错误数:{error_count}", end="")
            sys.stdout.flush()
        print('\n')
        
    elif scraper_choice == "3":
        print('\n开始爬取:https://cn.freevpnnode.com/')
        error_count = 0
        proxy_list = ProxyScraper("https://cn.freevpnnode.com/",
                        '<tr>.*?<td>(?P<ip>.*?)</td>.*?<td>(?P<port>.*?)</td>.*?<td><span>.*?</span> <img src=".*?" width="20" height="20" .*? class="js_openeyes"></td>.*?</td>',
                        ["ip", "port"]).scrape_proxies()
        if isinstance(proxy_list, list):
            all_proxies.extend(proxy_list)
        else:
            error_count += 1
        print(f'100%|██████████████████████████████████████████████████| 1/1  错误数:{error_count}')

    elif scraper_choice == "4":
        error_count = 0
        try:
            print('信息:共约7000页,建议一次爬取数量不大于500页,防止被封')
            start_page = int(input('爬取起始页（整数）：'))
            end_page = int(input("爬取结束页（整数）:"))
            if end_page < 1 or start_page < 1 or end_page > 7000 or start_page > 7000 or start_page > end_page:
                print("不能小于1或大于7000,起始页不能大于结束页")
                return

            print('开始爬取:https://www.kuaidaili.com/free/inha/')
            
            for page in range(start_page, end_page + 1):

                proxy_list = ProxyScraper(f"https://www.kuaidaili.com/free/inha/{page}/",
                                '{"ip": "(?P<ip>.*?)", "last_check_time": ".*?", "port": "(?P<port>.*?)", "speed": .*?, "location": ".*?"}',
                                ["ip", "port"]).scrape_proxies()
                if isinstance(proxy_list, list):
                    all_proxies.extend(proxy_list)
                else:
                    error_count += 1

                time.sleep(2)

                # 计算进度百分比
                current_page = page - start_page + 1
                total_pages = end_page - start_page + 1
                percent = current_page * 100 // total_pages
                # 计算进度条长度
                completed = current_page * 50 // total_pages
                remaining = 50 - completed
                # 处理百分比显示的对齐
                if percent < 10:
                    padding = "  "
                elif percent < 100:
                    padding = " "
                else:
                    padding = ""
                # 更新进度条
                print(f"\r{percent}%{padding}|{'█' * completed}{'-' * remaining}| {current_page}/{total_pages}  错误数:{error_count}", end="")
                sys.stdout.flush()
            print('\n')
        except:
            print("输入错误，请输入整数")

    elif scraper_choice == "5":

        print('\n开始爬取:http://www.ip3366.net/?stype=1')
        total_pages = 7
        error_count = 0
        for page in range(1, total_pages + 1):
            proxy_list = ProxyScraper(f'http://www.ip3366.net/?stype=1&page={page}',
                            '<tr>.*?<td>(?P<ip>.*?)</td>.*?<td>(?P<port>.*?)</td>.*?</tr>', ['ip', 'port']).scrape_proxies()
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1

            time.sleep(1)

            # 计算进度百分比
            percent = page * 100 // total_pages
            # 计算进度条长度
            completed = page * 50 // total_pages
            remaining = 50 - completed
            # 处理百分比显示的对齐
            if percent < 10:
                padding = "  "
            elif percent < 100:
                padding = " "
            else:
                padding = ""
            # 更新进度条
            print(f"\r{percent}%{padding}|{'█' * completed}{'-' * remaining}| {page}/{total_pages}  错误数:{error_count}", end="")
            sys.stdout.flush()
        print('\n')

    elif scraper_choice == "6":
        try:
            count = int(input("爬取个数(整数)："))
            if count < 1:
                print("数量必须大于0")
                return

            print(f"\n开始爬取 {count} 个代理...") 
            try:
                import aiohttp   # 协程
                import asyncio
                semaphore = asyncio.Semaphore(20)  # 最大并发
                timeout = aiohttp.ClientTimeout(total=50)  # 超时(给服务器足够响应时间)
                async def fetch_proxy(url):
                    
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(url=url) as response:
                            if response.status == 200:
                                proxy = await response.text()
                                print(proxy)
                                return proxy
                
                async def fetch_proxies_main():
                    url = 'https://proxypool.scrape.center/random'
                    async with semaphore:
                        tasks = [asyncio.create_task(fetch_proxy(url=url)) for _ in range(count)]
                        results  = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    return results
                # proxy = requests.get('https://proxypool.scrape.center/random', timeout=timeout).text.strip()
                proxies = asyncio.run(fetch_proxies_main())
                if len(proxies) > 0:
                    all_proxies = proxies
                    # print(all_proxies)
            except:
                pass

            print("\n爬取完成！")
        except:
            print("输入错误")

    elif scraper_choice == '7':
        error_count = 0
        url = 'https://proxy.scdn.io/text.php'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            'Referer':'https://proxy.scdn.io/'
        }
        try:
            response = requests.get(url,headers=headers)
            result = response.text.split("\n")
            proxy_list = []
            for proxy in result:
                if len(proxy) == 0:
                    print('没有代理可以爬取')
                else:
                    proxy_list.append(proxy.strip())
            if isinstance(proxy_list, list):
                all_proxies.extend(proxy_list)
            else:
                error_count += 1
            print(f'100%|██████████████████████████████████████████████████| 1/1  错误数:{error_count}')
        except Exception as e:
            print(f'爬取失败: {str(e)}')
    
    elif scraper_choice == '8':
        print('\n开始爬取:https://proxyhub.me/zh/cn-http-proxy-list.html')
        error_count = 0
        proxy_list = ProxyScraper("https://proxyhub.me/zh/cn-http-proxy-list.html",
                        r'<tr>\s*<td>(?P<ip>\d+\.\d+\.\d+\.\d+)</td>\s*<td>(?P<port>\d+)</td>',
                        ["ip", "port"]).scrape_proxies()
        if isinstance(proxy_list, list):
            all_proxies.extend(proxy_list)
        else:
            error_count += 1
        print(f'100%|██████████████████████████████████████████████████| 1/1  错误数:{error_count}')

    else:   # 退出
        print("退出")
        return None
    
    return filter_proxies(all_proxies)   # 返回筛选后的代理列表

def extract_proxies_menu():
    """提取代理菜单"""
    try:
        count = int(input("请输入要提取的代理数量: "))
        if count <= 0:
            print("数量必须大于0")
            return

        proxies = extract_proxies(count)
        if not proxies:
            print("代理池中没有可用代理")
            return

        if len(proxies) < count:
            print(f"⚠️ 警告: 只有 {len(proxies)} 个可用代理，少于请求的 {count} 个")

        print("\n提取的代理列表:")
        for i, proxy in enumerate(proxies, 1):
            print(f"{i}. {proxy}")

        save_choice = input("是否保存到文件? (y/n): ").lower()
        if save_choice == "y":
            filename = input("请输入文件名: ")
            with open(filename, "w", encoding="utf-8") as file:
                for proxy in proxies:
                    file.write(f"{proxy}\n")
            print(f"已保存到 {filename}")
    except ValueError:
        print("请输入有效的数字")

if __name__ == '__main__':
    while True:
        print(f"""功能：
        1: 爬取并验证新代理 (添加到代理池)
        2: 检验并更新代理池中的代理分数
        3: 提取指定数量的代理
        4: 查看代理池状态
        5: 从csv文件加载并验证(ip,port)

        输入其他: 退出
        """)
        choice = input("选择：")

        if choice == "1":
            new_proxies = crawl_proxies()
            if new_proxies:
                validate_new_proxies(new_proxies)
        elif choice == "2":
            validate_existing_proxies()
        elif choice == "3":
            extract_proxies_menu()
        elif choice == "4":
            proxies = load_proxies_from_file(OUTPUT_FILE)
            total = len(proxies)
            if total == 0:
                print("代理池为空")
            else:
                # 统计不同分数的代理数量
                score_count = {}
                for score in proxies.values():
                    score_count[score] = score_count.get(score, 0) + 1

                # 按分数排序
                sorted_scores = sorted(score_count.items(), key=lambda x: x[0], reverse=True)

                print(f"\n代理池状态 ({OUTPUT_FILE}):")
                print(f"总代理数量: {total}")
                print("分数分布:")
                for score, count in sorted_scores:
                    print(f"  {score}分: {count}个代理")

                # # 感觉下面这个功能没必要
                # # 显示分数最高的10个代理
                # top_proxies = sorted(proxies.items(), key=lambda x: x[1], reverse=True)[:10]
                # print("\n分数最高的10个代理:")
                # for i, (proxy, score) in enumerate(top_proxies, 1):
                #     print(f"{i}. {proxy} - {score}分")
                print('='*20)
                print(f'共 {total} 个代理')   # TTY不能上滚终端,将主要数据在下方显示一遍 
        elif choice == '5':
            try:
                filename = input('文件名(路径):')
                data = []

                with open(filename,'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        data.extend(row)
                        
                all_proxies = [f"{data[i].strip()}:{data[i + 1].strip()}" for i in range(0, len(data), 2)]
                new_proxies = filter_proxies(all_proxies)   # 去掉重复的,错误的
                validate_new_proxies(new_proxies)

            except:
                print('出错了')
        
        else:
            print('退出')
            break
