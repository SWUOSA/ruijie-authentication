# 西南大学校园外网自动登录脚本

#### 2023/11/14 应对密码加密更新
系统更新之后整体的逻辑没变，但必须使用加密后的密码才能登录，这样确实也能提高安全性（不会被中间人抓包直接获取明文的账号密码
<br>对应下面的第4点

---

- 协会的服务器需要登录校外网，之前一直用的定时包重放，麻烦的一批，实在是忍不了了，用 Fiddler4 抓了整个过程的包写了一个 Python 脚本。

需要 requests 和 gmpy2 库，如果没有，用 pip(Win or Linux) 或者 apt(Linux) 安装

```bash
pip install requests gmpy2
# apt install python3-requests python3-gmpy2
```

修改账号密码为自己的，如果做定时自动登录可以把日志的注释取消了，设置一个路径

要实现定时自动执行，Windows 可以用自带的 任务计划程序；Linux 下可以用 cron

学校用的是锐捷的系统，和其他用锐捷的登录过程基本差不多，大概过程如下：

0. 访问指定的网址，没登陆被重定向到 http://222.198.127.170
1. 请求 http://222.198.127.170 ，获取到一个 cookie JSESSIONID，状态码为 302，然后通过相应设定的 Location 重定向到 http://222.198.127.170/eportal/gologout.jsp
2. 这里会判断是不是已经登录过了，如果登录过了就重定向到 http://222.198.127.170/eportal/./success.jsp
   <br>如果是绑定了MAC地址，好像是重定向到 /eportal/redirectortosuccess.jsp，没验证，有兴趣可以试试
   <br>如果没有登录，重定向至 http://123.123.123.123 注册设备，返回一段 script 代码又重定向
3. 这个重定向浏览器会自动跳转，显示出来就是登录的那个界面；脚本这里因为不是 302 不会自动的重定向，需要提取 script 里面的 url 动手写一个 get 请求跳转
   <br>实际上 3 这一步在脚本中没有意义，只需要提取 2 中返回的那段 script 代码中的参数就是最后登录时的要用的 queryString 参数，，加上这一步是为了尽量模拟浏览器的行为以应对可能行为检测（虽然暂时还没有
4. 密码使用 RSA 加密，通过请求 /eportal/InterFace.do?method=pageInfo 获取 RSA 公钥，然后才能将密码加密发给服务器
   <br>这套密码机制也不是新更新的，最开始也有，只是之前服务区端没有强制开启
   <br>分析 js 可以看到当浏览器勾选记住密码时，会使用这套加密机制将明文加密存储在网站的 cookie 中
   <br>在加密时并不是直接将密码加密，而是加密：密码+'>'+设备MAC地址
5. 使用上面获取的 queryString、自己的账号和加密后的密码登录

代码鲁棒性不不咋地，但也够用了。

感兴趣可以自己抓一下整个过程，懒得抹信息，fiddler 抓到的包我就不传了。

觉得 Python 麻烦可以直接抓登录最后的那个 /eportal/InterFace.do?method=login 的包直接用 Curl 重放也行 ~~（我觉的这样更麻烦）~~

但应该不能拿到其他设备直接重放，中间请求 123.123.123.123 的时候应该是有一个设备注册的过程 ~~（yy的，没测试）~~

---
没有加密支持，可能有空会改改，大概吧（
<br>~~添加一个别处找的锐捷登录通用 shell 脚本，需要先安装 Curl。
其他学校只需要改一下 service 参数应该就可以了
使用方法~~
```bash
chmod +x ruijie_general.sh 
./ruijie_general.sh "user" "passwd"
```
