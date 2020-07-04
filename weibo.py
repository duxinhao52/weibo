import requests
from pyquery import PyQuery as pq
import json
from pymongo import MongoClient

#首先要连接上数据库再进行插入操作，而不是放在循环中每次都连接！
#无须先在mongodb中创建库和集合，会自动创建！
#mongo进入服务，show dbs显示出所有的库，use切换到库，db.集合名.find()显示数据！
client=MongoClient(host='localhost',port=27017) #连接mongodb数据库
db=client['weibolist']  #选择数据库
collection=db['weibo']  #选择库中的集合
max_page=25
base_url='https://m.weibo.cn/api/container/getIndex?'
headers={
    'Referer': 'https://m.weibo.cn/u/2830678474',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'        #分辨出是Ajax请求的关键
}
def get_one_page(since_id):
    params={
        'type': 'uid',
        'value': '2830678474',
        'containerid': '1076032830678474',
    }
    if since_id!='':
        params['since_id']=since_id
    try:
        response=requests.get(base_url,params=params,headers=headers)
        if response.status_code==200:
            return response.json()              #请求返回的是JSON格式的str类型，所以要解析
        return None
    except requests.RequestException:
        return None
def parse_one_page(text):
    if text:
        items=text.get('data').get('cards')
        for item in items:
            item=item.get('mblog')
            weibo={}
            weibo['id'] = item.get('id')
            weibo['text'] = pq(item.get('text')).text()    #pq的text()方法可以删除文本内的html代码
            weibo['attitudes'] = item.get('attitudes_count')
            weibo['comments'] = item.get('comments_count')
            weibo['reposts'] = item.get('reposts_count')
            yield weibo
def write_to_file(item):
    with open('ret.txt','a',encoding='utf-8') as f:
        f.write(json.dumps(item,ensure_ascii=False)+'\n')   #字典序列化，可写入文件,ensure_ascii可写入中文
def save_to_mongodb(item):
    if collection.insert(item):
        print('Saved to Mongo')
if __name__=='__main__':
    since_id=''
    for page in range(1,max_page+1):     #max_page为请求次数
        text=get_one_page(since_id)
        since_id=text.get('data').get('cardlistInfo').get('since_id')   #拿到下次的since_id
        for item in parse_one_page(text):
            write_to_file(item)
            save_to_mongodb(item)
    db.close()