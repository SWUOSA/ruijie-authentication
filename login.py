# -*- coding: utf-8 -*-
import time
import requests # requests库没有需要pip install requests
import gmpy2 # 大数运算库，用来算RSA的pip install gmpy2

# 挺简单的一个过程，懒得写函数了

# 账号密码，不懂的只需要修改这里
user = "user"
passwd = "passwd"
# log_path = "c:/Users/1234/login.log" # 日志的位置

# 这个IP对应域名login.swu.edu.cn
ip = "222.198.127.170"
url = "http://" + ip

# file = open(log_path, 'a')

session = requests.session()
session.headers = {
    'Host': ip,
    'Connection': "keep-alive",
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    'Accept-Encoding': "gzip, deflate",
    'Accept-Language': "zh-CN,zh;q=0.9"
}

# 这里没有关闭重定向，默认allow_redirects=True，实际上进行了多次跳转，流程大致如下：
# 1、请求 http://222.198.127.170，获取到一个cookie JSESSIONID，状态码为302，然后通过相应设定的Location重定向到http://222.198.127.170/eportal/gologout.jsp，如果是
# 2、这里会判断是不是已经登录过了，如果登录过了就重定向到http://222.198.127.170/eportal/./success.jsp；如果没有登录，重定向至 http://123.123.123.123 注册设备，返回一段script代码又重定向
# 3、这个重定向浏览器会自动跳转，显示出来就是登录的那个界面；脚本这里因为不是302不会自动的重定向，需要提取script里面的url动手写一个get请求跳转；
# 实际上3这一步在脚本中没有意义，只需要提取2中返回的那段script代码中的参数就是最后登录时的要用的queryString参数，加上这一步是为了尽量模拟浏览器的行为以应对可能行为检测（虽然暂时还没有

# 2023/11/14 
# 系统更新之后必须使用加密后的密码才能登录，这样确实也能提高安全性（不会被中间人抓包直接获取明文的账号密码
# 4、密码使用RSA加密，通过请求/eportal/InterFace.do?method=pageInfo获取RSA公钥，然后才能将密码加密发给服务器
# 这套密码机制也不是新更新的，最开始也有（分析js可以看到当浏览器勾选记住密码时，会使用这套加密机制将明文加密存储在网站的cookie中），只是之前服务区端没有强制开启
# 在加密时并不是直接将密码加密，而是：密码+'>'+设备MAC地址
# 5、使用上面获取的queryString、自己的账号和加密后的密码登录

response = session.get(url)

# 如果重定向到了/eportal/./success.jsp说明已经登录过了
# 如果是绑定了MAC地址，好像是跳转到/eportal/redirectortosuccess.jsp，没验证，有兴趣的可以试试
if('userIndex' in response.url and 'success' in response.url):
    msg = time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()) + "用户已在线\n"
    print(msg)
    # file.write(msg)
    # file.close()
    session.close()
    exit(0)

# 获取设备的一些信息，内网地址啥的，应该也会根据请求的参数进行设备注册
# print(response.text)
str = response.text
redirect_url =  str[str.find("http"):str.find("'</script>")]
query_str = redirect_url[redirect_url.find("index.jsp")+10:]
# print(redirect_url, query_str)
mac_str = redirect_url[redirect_url.find("mac=")+4:][:12]
# print(mac_str)

# 这一步可以不要，就是第3步
session.headers['Referer'] = 'http://123.123.123.123/'
# print(session.headers)
session.get(redirect_url)

# 获取RSA公钥
post_data = {
    'queryString': query_str
}
path = url + '/eportal/InterFace.do?method=pageInfo'
responese = session.post(path, post_data)
response.encoding = "utf-8"
resultJson = responese.json()
rsa_e = int(resultJson['publicKeyExponent'], 16)
rsa_n = int(resultJson['publicKeyModulus'], 16)
# print(hex(rsa_e), hex(rsa_n))
secret = passwd + '>' + mac_str
passwd_encrypted = hex(gmpy2.powmod(int.from_bytes(secret.encode()), rsa_e, rsa_n))[2:]
# print(passwd_encrypted)

# 用前面获取的参数登录
session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
session.headers['Origin'] = url
session.headers['Referer'] = response.url
session.cookies['EPORTAL_COOKIE_OPERATORPWD'] = ''
# print(session.headers, session.cookies)
post_data = {
    'userId': user,
    'password': passwd_encrypted,
    'service': '默认',
    'queryString': query_str,
    'operatorPwd': '',
    'operatorUserId': '',
    'validcode': '',
    'passwordEncrypt': 'true'
}
path = url + '/eportal/InterFace.do?method=login'
response = session.post(path, data=post_data)

response.encoding = "utf-8"
resultJson = response.json()
# 登录是否成功
if(resultJson['result'] == 'success'):
    msg = time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()) + user + " 登录成功\n"
else:
    msg = time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()) + user + " 登录失败: " + resultJson['message'] + "\n"

print(msg)
# file.write(msg)
# file.close()
session.close()

# 觉得Python麻烦可以直接抓登录最后的那个/eportal/InterFace.do?method=login的包直接用Curl重放也行
# 但应该不能拿到其他设备直接重放，中间请求123.123.123.123的时候应该是有一个设备注册的过程（yy的，没测试）
# 要实现定时自动执行脚本，Windows可以用自带的工具，开始菜单找 任务计划程序，Linux下可以用cron
