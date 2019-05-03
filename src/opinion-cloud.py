#%% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
import os
try:
	os.chdir(os.path.join(os.getcwd(), 'src'))
	print(os.getcwd())
except:
	pass

#%%
import requests, json, urllib3,re, sys, jieba, operator, collections, math
from bs4 import BeautifulSoup
from six import u
from udicOpenData.stopwords import *


#%%
urllib3.disable_warnings()
payload = {'from':'/bbs/Gossiping/index.html','yes':'yes'}
url = 'https://www.ptt.cc/bbs/Gossiping/index.html'
rs = requests.session()
res = rs.post('https://www.ptt.cc/ask/over18',data=payload)


#%%
threshold =5000
politic_name = ['柯文哲','柯p','北市長','柯媽','陳佩琪','柯P','柯']
p_name = '柯'


#%%
url = 'https://www.ptt.cc/bbs/Gossiping/index.html'
path_output = '../asset/gossip_output.json'
path_kop = '../asset/gossip_kop.json'
path_pdf = '../output/gossip.pdf'
path_link = '/bbs/Gossiping/'


# url = 'https://www.ptt.cc/bbs/HatePolitics/index.html'
# path_output = '../asset/hatepolitics_output.json'
# path_kop = '../asset/hatepolitics_kop.json'
# path_pdf = '../output/hatepolitics.pdf'
# path_link = '/bbs/HatePolitics/'


#%%
def check_name(keyword,content):
    for word in keyword:
        if word in content:
            return 1
        else:
            return 0
        
def sort_dict(dict):
    sorted_x = sorted(dict.items(), key=lambda kv: kv[1], reverse=True)
    sorted_dict = collections.OrderedDict(sorted_x)
    
    return list(sorted_dict.items())

#%% [markdown]
# # 開爬

#%%
article_count = 0
page = 0
with open(path_output, 'w',encoding = 'utf8')as f:
    f.truncate(0)
f.close()
while article_count < threshold:
    res = rs.get(url, verify=False)
    soup = BeautifulSoup(res.text)
    nextpageurl = 'https://www.ptt.cc'+soup.find_all(attrs = {'class':'btn wide'})[1]['href']#下一頁以及上一頁url
    print('current url:',url)
    print('next url:',nextpageurl)
    for article in soup.find_all('div', class_='r-ent'):
#         print('aaaaaaaaaaaa')
#         print(article)
        push_content = []
        if article_count >= threshold:
            break
        meta = article.find(class_='title')
        text = meta.find('a')
        if(text is not None):
            title = text.text
            if '公告' not in title:
            
                link = meta.find('a')['href']
                date = article.find('div', 'date').getText()
                author = article.find('div', 'author').getText()
                article_id = link.replace(path_link,'').replace('.html','')

                #蒐集內文資料
                contenturl = "https://www.ptt.cc" + link
                res = rs.get(contenturl)
                soup = BeautifulSoup(res.text, 'lxml')

                main_content = soup.find(id="main-content")
                metas = main_content.select('div.article-metaline')
                
                #去除main_content中非內文部分
                for meta in metas:
                    meta.extract()
                for meta in main_content.select('div.article-metaline-right'):
                    meta.extract()
                pushes = main_content.find_all('div', class_='push')
                for push in pushes:
                    push.extract()
                try:
                    ip = main_content.find(text=re.compile(u'※ 發信站:'))
                    ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
                except:
                    ip = "None"
                filtered = [ v for v in main_content.stripped_strings if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--'] ]
                expr = re.compile(u(r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))
                for i in range(len(filtered)):
                    filtered[i] = re.sub(expr, '', filtered[i])

                filtered = [_f for _f in filtered if _f]  # remove empty strings
                filtered = [x for x in filtered if article_id not in x]  # remove last line containing the url of the article

                #蒐集留言(存入list)    
                for push in pushes:
                    try:
                        push_content.append(push.find('span',class_='push-content').get_text().encode(sys.stdin.encoding, "replace").decode(sys.stdin.encoding))
                    except Exception:
                        push_content.append('')
                        print('error')
                        pass


                #蒐集內文
                content = ' '.join(filtered)
                content = re.sub(r'(\s)+', ' ', content)



                article_count += 1
                #將蒐集到的資料儲存成json格式
                data = {'number':article_count,
                        'author':author,
                        'title':title,
                        'content':content,
                        'comment':push_content
                        }
                #印出資料、儲存至json
                with open(path_output, 'a',encoding = 'utf8')as f:
                    json.dump(data,f, ensure_ascii=False,indent = 4, separators=(',', ': '))
                f.close()
                print("count:",article_count,":",title, date, author)  # result of setp-3
                #print(content)
                #print(main_content.extract())
                #print(data)
            
            
            
    url = nextpageurl
    page+=1
    print("================page ",page,' ===================')
    


#%%
#seg_list = jieba.cut(data['content'], cut_all=False)
seg_list = list(rmsw(data['content'], flag=True))
#print("Full Mode: " + "/ ".join(seg_list))
seg_dic = {}
for seg in seg_list:
    if seg not in seg_dic.keys():
        seg_dic[seg[0]] = 0
    seg_dic[seg[0]] += 1
print(seg_dic)
print('')
sorted_x = sorted(seg_dic.items(), key=lambda kv: kv[1], reverse=True)
#sorted_x = sorted_x.reverse()
sorted_dict = collections.OrderedDict(sorted_x)
print(sorted_dict)

#%% [markdown]
# # 開讀

#%%
with open(path_output, 'r', encoding='utf-8') as infile:
    data = infile.read()
    data = data.replace('}{', '}\n\n{')
    data = data.split('\n\n')
    article_list = []
    for i in data:
        article_list.append(json.loads(i))
    infile.close()
original_article_list = article_list


#%%
global_keyword = {} #{關鍵字:出現文章數}


#%%
#Append frequency into article list
# jieba.suggest_freq('柯文哲', True)
# jieba.suggest_freq('郭董', True)
for name in politic_name:
    jieba.suggest_freq(name, True)
for article in article_list:
    print(article['number'])
    art = article['title'] + '\n' + article['content'] + '\n' + str(article['comment'])
#    art = article['title'] + '\n' + article['content'] 
    #seg_list = jieba.lcut(art, cut_all=False)
    seg_list = []
    tmp_list = list(rmsw(art, flag=True))
    for i in tmp_list:
        seg_list.append(i[0])
    #print("Full Mode: " + "/ ".join(seg_list))
    seg_dict = {}
    for seg in seg_list:
        if seg not in seg_dict.keys():
            seg_dict[seg] = 0
        seg_dict[seg] += 1
    #print(seg_dic)
    #print('')
    #sorted_x = sorted(seg_dic.items(), key=lambda kv: kv[1], reverse=True)
    #sorted_x = sorted_x.reverse()
    #sorted_dict = collections.OrderedDict(sorted_x)
    #print(sorted_dict)
    freq_count = 0
    for i in seg_dict:
        freq_count += seg_dict[i]
        if i not in global_keyword.keys():
            global_keyword[i] = 1
        else:
            global_keyword[i] += 1
    #article['frequency'] = list(sorted_dict.items())
    article['frequency'] = seg_dict
    article['freq_count'] = freq_count
    article['keyword'] = seg_list
#print(article_list)
print('-----------------------')
print(article_list[0])
print('-----------------------')
print(global_keyword)


#%%
for article in article_list:
    tfidf_dict = {}
    for keyword in article['keyword']:
        tfidf_dict[keyword] = round((article['frequency'][keyword]/article['freq_count'])                                     * math.log(threshold/global_keyword[keyword],10), 5)  
        tfidf_dict[keyword]*=10000
        if tfidf_dict[keyword] <= 0:
            tfidf_dict.pop(keyword,None)
        
    article['tfidf'] = tfidf_dict
#print(article_list[44])
print('--------------')
print(sort_dict(article_list[0]['tfidf'])[:10])
print('--------------')


#%%
global_tfidf = {}
with open(path_kop, 'w',encoding = 'utf8')as f:
    f.truncate(0)
f.close()

kop_count = 0

for article in article_list:
    signal = 0
    
    #篩選出只有politic name相關的文章
    for name in politic_name:
        for key in sort_dict(article['tfidf'])[:10]:
            if name in key:
                signal = 1
                
                
    if signal ==1:
        for tfidf in article['tfidf']:
            if tfidf not in global_tfidf.keys():
                global_tfidf[tfidf] = 0
            if article['tfidf'][tfidf] > global_tfidf[tfidf]:
                    global_tfidf[tfidf] = article['tfidf'][tfidf]
                    #print(global_tfidf[keyword])
            if global_tfidf[tfidf] <= 0:
                tfidf_dict.pop(keyword,None)
        
        new = {'number':article['number'],
               'title':article['title'],
               'tfidf':sort_dict(article['tfidf'])[:10]}
        with open(path_kop, 'a',encoding = 'utf8')as f: 
            json.dump(new,f, ensure_ascii=False,indent = 4, separators=(',', ': '))
            f.close()
        kop_count += 1
print('Article about 柯文哲 shows '+str(kop_count)+' articles')     
print(sort_dict(global_tfidf)[:100])


#%%
from PIL import Image
import matplotlib.pyplot as plt
from wordcloud import WordCloud, ImageColorGenerator
import numpy as np
#%% 
import cv2
#%%
import cv2
#中文繪圖需要中文字體，請自己從windows font目錄抓
#微軟正黑體
font = '../asset/black.ttf'
#想要文字雲出現的圖示
mask = np.array(Image.open("../asset/kop.jpg"))
ret,mask = cv2.threshold(mask,127,255,cv2.THRESH_BINARY_INV)
#背景顏色預設黑色，改為白色
#mark改用五月天的皇冠
#其他參數請自行參考wordcloud
my_wordcloud = WordCloud(background_color="white",mask=mask,font_path=font,collocations=False, width=mask.shape[1], height=mask.shape[0], margin=2)  
my_wordcloud.generate_from_frequencies(frequencies=global_tfidf)
 
#產生圖片
#plt.figure( figsize=(10,10))
plt.imshow(my_wordcloud,interpolation='bilinear')
plt.axis("off")
plt.tight_layout(pad=-25)
#顯示用
plt.savefig(path_pdf,dpi=600,bbox_inches="tight")
plt.show()


#%%



