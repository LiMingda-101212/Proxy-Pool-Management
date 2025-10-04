# 总述

支持http/https/socks4/socks5

### 功能介绍:

本程序用于代理管理,有以下几个功能:

1.爬取和验证新代理,并将通过的代理添加到代理池文件(OUTPUT_FILE).新代理使用自动检测类型.为了使每个代理得到充分使用,本程序采取新代理验证两遍的策略,只要有一次通过即算通过,确保不会落下任何一个可用代理.
    在验证之前会先将重复代理,错误代理筛除,确保不做无用功.满分100分,有效代理验证成功默认分数98分,超时代理80分,错误代理和无效代理0分(会被0分清除函数清除).
    
2.检验和更新代理池内代理的有效性,使用代理池文件中的Type作为类型,再次验证成功加1分,超时代理分不变,无效代理和错误代理减1分,更直观的分辨代理的稳定性.

3.提取指定数量的代理,优先提取分数高,稳定的代理,可指定提取类型

4.查看代理池状态(总代理数量,各种类型代理的分数分布情况)

5.从csv文件(ip,port格式)加载并验证代理,用于手动添加代理时使用,可以选择代理类型(这样比较快),也可用自动检测(若用自动检测可能较慢)

代理池文件格式(OUTPUT_FILE) -> csv

Type,Proxy:Port,Score

类型,代理:端口,分数

建议将此程序放到proxies文件夹下,如果想放到其他地方,请修改'OUTPUT_FILE = "../proxies/valid_proxies.csv"'中的proxies为你的文件夹名称

# 代理管理程序执行流程

## 程序概述
本程序是一个功能完整的代理管理工具，支持HTTP/HTTPS/SOCKS4/SOCKS5协议的代理验证和管理。

## 主要执行流程

### 1. 程序启动
```python
if __name__ == '__main__':
    # 显示主菜单，等待用户选择功能
    while True:
        显示功能菜单
        获取用户选择
        根据选择执行相应功能
```

### 2. 功能1：爬取并验证新代理 (自动检测类型)
```
main → 选择1 → crawl_proxies() → validate_new_proxies() → check_proxies_batch() → check_proxy()
```

**详细流程:**
1. `crawl_proxies()`: 显示可爬取的网站列表，用户选择后开始爬取
2. `ProxyScraper.scrape_proxies()`: 使用正则表达式从网站爬取代理IP和端口
3. `filter_proxies()`: 过滤掉重复代理和无效格式的代理
4. `validate_new_proxies()`: 使用自动检测类型验证新代理
5. `check_proxies_batch()`: 批量验证代理（新代理验证两次）
6. `check_proxy()`: 单个代理验证，自动检测协议类型(HTTP→SOCKS5→SOCKS4)
7. 合并验证结果到现有代理池
8. 保存有效代理到CSV文件并显示统计信息

### 3. 功能2：检验并更新代理池中的代理分数
```
main → 选择2 → validate_existing_proxies() → check_proxies_batch() → check_proxy()
```

**详细流程:**
1. `load_proxies_from_file()`: 从CSV文件加载现有代理和类型
2. `validate_existing_proxies()`: 使用文件中记录的类型验证代理
3. `check_proxies_batch()`: 批量验证代理（已有代理验证一次）
4. `check_proxy()`: 单个代理验证，使用指定类型
5. 更新代理分数：成功+1分，失败-1分，超时不变
6. 移除0分代理
7. 保存更新后的代理池

### 4. 功能3：提取指定数量的代理 (支持类型筛选)
```
main → 选择3 → extract_proxies_menu() → extract_proxies_by_type()
```

**详细流程:**
1. `extract_proxies_menu()`: 获取用户输入的提取数量和类型
2. `extract_proxies_by_type()`: 按类型筛选并按分数排序
3. `load_proxies_from_file()`: 加载代理池数据
4. 返回格式为：`协议://ip:port`
5. 可选择保存到文件

### 5. 功能4：查看代理池状态
```
main → 选择4 → show_proxy_pool_status()
```

**详细流程:**
1. `load_proxies_from_file()`: 加载代理池数据
2. `show_proxy_pool_status()`: 按类型分组统计
3. 显示每种类型的代理数量和分数分布
4. 显示总代理数量

### 6. 功能5：从csv文件加载并验证代理 (支持类型选择)
```
main → 选择5 → load_from_csv_with_type() → validate_new_proxies_with_type()/validate_new_proxies()
```

**详细流程:**
1. `load_from_csv_with_type()`: 获取文件路径和代理类型选择
2. 读取CSV文件（支持`ip,port`或`ip:port`格式）
3. `filter_proxies()`: 过滤重复代理
4. 根据选择调用相应验证函数：
   - 指定类型：`validate_new_proxies_with_type()`
   - 自动检测：`validate_new_proxies()`
5. 保存验证结果到代理池

## 核心函数调用关系

### 验证流程
```
validate_new_proxies() / validate_new_proxies_with_type()
    ↓
check_proxies_batch(max_workers=30)
    ↓
ThreadPoolExecutor → check_proxy() [并发执行]
    ↓
requests.get() with proxies配置
    ↓
返回 (代理, 是否可用, 响应时间, 检测到的类型)
```

### 数据流
```
网络爬取/文件读取 → ProxyScraper → filter_proxies() → 验证函数 → save_valid_proxies() → CSV文件
```

## 关键特性

1. **智能类型检测**: 新代理自动检测协议类型(HTTP→SOCKS5→SOCKS4)
2. **分数机制**: 成功代理98分，超时代理80分，动态调整分数
3. **并发验证**: 使用线程池(MAX_WORKERS=30)提高验证效率
4. **去重处理**: 自动过滤重复代理
5. **多种数据源**: 支持从8个网站爬取和CSV文件导入
6. **灵活提取**: 可按类型和分数提取代理
7. **完整统计**: 提供详细的类型和分数统计信息

## 文件格式
```
Type,Proxy:Port,Score
http,192.168.1.1:8080,98
socks5,10.0.0.1:1080,95
```

本程序提供了一个完整的代理生命周期管理解决方案，从获取、验证到维护和使用都有完善的功能支持。
