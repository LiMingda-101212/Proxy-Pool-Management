zh-CN  --  Chinese  -- 简体中文
### 功能介绍:
#### 本程序用于代理管理,有以下几个功能:
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
### Function Introduction:
#### This program is used for proxy management and has the following functions:
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
