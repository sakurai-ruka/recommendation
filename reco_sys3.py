#システム概要
#システムとユーザが会話を行い、商品推薦を行うシステム
#商品推薦時には商品とユーザの要望のマッチ度を理由として説明する.
import openai
import os
from langchain import PromptTemplate
from langchain import FewShotPromptTemplate
#from langchain.llms import OpenAI
#from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import OpenAI
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
import random

# Assign OpenAI API Key from environment variable
openai.organization = ""
openai.api_key = ''
os.environ['OPENAI_API_KEY'] = ''
messages = []
keyword_list = []
keyword2 = []
keyword_sublist = []
system_msg = "シナリオに沿って会話をするシステム,\
1.最初にユーザが何の商品を求めているか聞く,\
2.ユーザが求めている商品の詳細を聞く.\
3.商品によって、産地、ブランド、素材等を聞く.\
4.勝手に商品の推薦は行わない."
messages.append({"role": "system", "content": system_msg})
print("Say hello to your new assistant!")

#キーワード抽出処理
examples = [
    {"text": "服が欲しいです", "keyword": "服"},
    {"text": "赤身のお肉が良いです", "keyword": "赤身,お肉"},
    {"text": "4000円以下がいいです", "keyword": "4000円以下"},
    {"text": "今日は魚よりも肉の気分", "keyword": "肉"},
    {"text": "夏だから薄目の服が欲しい", "keyword": "薄目,服"},
    {"text": "こんにちは", "keyword": "なし"},
    {"text": "今日は天気良いですね", "keyword": "なし"},
    {"text": "お腹がすきました", "keyword": "なし"},   
    {"text": "北海道とかいいですね", "keyword": "北海道"},
]
example_formatter_template = """
text: {text}
keyword: {keyword}
"""
example_prompt = PromptTemplate(
    template=example_formatter_template,
    input_variables=["text", "keyword"]
)
few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix="要求されている商品の内容を教えて",
    suffix="text: {input}\nkeyword: ",
    input_variables=["input"],
    example_separator="\n\n",
)

#必要なキーワードの取捨選択
examples2 = [
    {"text": "お肉,牛肉", "keyword": "牛肉"},
    {"text": "牛肉,赤身肉", "keyword": "牛肉,赤身肉"},
    {"text": "産地,国産", "keyword": "国産"},
    {"text": "服,パーカー", "keyword": "パーカー"},
    {"text": "食品,お肉", "keyword": "お肉"},
    {"text": "食品,魚", "keyword": "魚"},
    {"text": "お肉,牛肉，国産,6000円程度,モモ肉", "keyword": "牛肉,国産,6000円程度,モモ肉"},
    {"text": "牛肉,神戸牛", "keyword": "神戸牛"},
    {"text": "豚肉,豚バラ", "keyword": "豚バラ"},
    {"text": "神戸牛,牛モモ肉", "keyword": "神戸牛,牛モモ肉"},
]

few_shot_prompt2 = FewShotPromptTemplate(
    examples=examples2,
    example_prompt=example_prompt,
    prefix="必要な商品の内容を取捨選択して",
    suffix="text: {input}\nkeyword: ",
    input_variables=["input"],
    example_separator="\n\n",
)

#商品名を生成
examples3 = [
    {"text": "ジップアップパーカー メンズ 秋服 長袖 薄手 前開きパーカー トップス 無地 パーカ フード付き スポーツ おしゃれ", "keyword": "スポーツメンズ薄手ジップアップ前開きパーカー"},
    {"text": "【水・ミネラルウォーター】LOHACO Water 410ml 1箱（20本入）ラベルレス オリジナル", "keyword": "LOHACO Water410ml 1箱（20本入り）ラベルレスオリジナルミネラルウォーター"},
    {"text": "送料込み 日本一の和牛鹿児島黒牛切り落とし400g お取り寄せ 肉 お肉", "keyword": "送料込み！日本一の和牛鹿児島黒牛切り落とし400g"},
    {"text": "中古（目立った傷や汚れなし） PS4／ファイナルファンタジーＶＩＩ リメイク （FF7）", "keyword": "中古PS4ファイナルファンタジーVII リメイク"},
    {"text": "牛肉 肉 焼肉 和牛 「近江牛 特上焼肉 1kg」 御祝 内祝 ギフト プレゼント", "keyword": "近江牛 特上焼肉 1kg ギフトセット"},
    {"text": "父の日 ギフト 福井名物 焼さば寿司 ×3本(8貫/カット済み) 焼き鯖寿司 焼鯖 焼サバ 焼きサバ 焼きさば FF", "keyword": "父の日ギフト！福井名物焼さば寿司 ×3本（8貫/カット済み）"},
    {"text": "バッグ ウエストポーチ 【THE NORTH FACE/ザノースフェイス】Lumbnical-S(ラムニカル-S)", "keyword": "ザノースフェイス ラムニカル-S ウエストポーチバッグ"},
    {"text": "鮮魚 刺身用 柵 4種 詰め合わせ 『 朝獲れ 厳選4種類 三浦半島 刺身セット 』送料無料 鮮魚ボックス 早鈴直売所 下処理 サク 魚 地魚 お祝い 父の日", "keyword": "朝獲れ 三浦半島 刺身セット『鮮魚ボックス』"}, 
    {"text": "BBQ 冷凍野菜ミックス 3人前 北海道 バーベキュー じゃがいも かぼちゃ とうもろこし 冷凍野菜 バーベキュー 鉄板焼き用野菜セット 300ｇ BBQ 冷凍", "keyword": "北海道 BBQ 冷凍野菜ミックス、バーベキュープレミアムセット"},
    {"text": "バスク チーズケーキ 個包装 ミニ サイズ ４個 入り 送料無料 父の日 ギフト 誕生日 お中元 プレゼント お取り寄せ 高級 チーズケーキ ギフト スイーツ 内祝", "keyword": "高級バスク チーズケーキミニ 4個入りギフトセット"},       
]

few_shot_prompt3 = FewShotPromptTemplate(
    examples=examples3,
    example_prompt=example_prompt,
    prefix="入力された商品情報から商品名を生成して",
    suffix="text: {input}\nkeyword: ",
    input_variables=["input"],
    example_separator="\n\n",
)
examples4 = [
    {"text": "生地が恐ろしく薄い。1,000円のＹシャツよりも薄い。一度洗濯すると恐ろしくシワシワ。とても5,000円の価値があるとは思えない。殿堂入り商品とあるが、本当なのだろうか？。", "評価":"非常に不満", "理由":"生地が薄く、一度洗濯するとシワシワになり、その価値が5,000円であるとは思えないということ。"},
    {"text": "普段ゲームをあまりしませんがかなりの時間をやり込みました。無双なのでひたすらアクションではありますが、ストーリーを進めることができ、前作とのつながりが分かるので非常に面白かったです。ただ前作ほどの新鮮感はやはり無いですね。", "評価":"非常に面白い", "理由":"ストーリーが理解でき、時間をやり込むことでゲームの面白さを実感しているため。ただ前作に比べると新鮮感が薄いとされている。"},
    {"text": "すごくコンパクトなのに普通のエコバッグより大きめでたくさん荷物が入ります。想像以上かも。それが3つも届いてこの価格はありがたい", "評価":"大変高い評価", "理由":"コンパクトなのに普通のエコバッグより大きく収容量が大きく、想像以上の大きさで、3つも届き、値段もお手頃だったから。"},
    {"text": "初めは文字盤40ミリ大きく感じましたが、日付の文字も見やすいのでとても使いやすいです。グレーを一度注文しようとした時に品切れでしたが、日を改めてサイトを見たときに在庫になっていたので即注文しました。服にも合わせやすい色なので助かっています。", "評価":"高評価", "理由":"文字盤が見やすく、色が服にも合わせやすかったことが理由で高評価を得ている。"},
    {"text": "すぐはきつぶしてしまうので、購入しました。色合いも想像通りでサイズ感もいいです。また、見た目だけではなく歩きやすく疲れづらいような気がしてます。ビジネスシューズは割とすぐ買うことが多いので、こちらおすすめさせていただきます。", "評価":"高評価 ", "理由":"お求めやすい価格でサイズ感、見た目、歩きやすさが良く、ビジネスシューズとしておすすめだと感じたため。"},
    {"text": "実家への贈答品として送り、今回、帰省した際に飲ませてもらいました。獺祭は、よく購入して飲んでいますが、こんなまずいのは初めてです。大吟醸なのに、人工アルコールのような味が・・・非常に残念です。販売店は悪くないのかもしれませんが、最近は流通ルートに偽物も流れていると聞きますので、注意された方が良いと思います。", "評価":"非常に残念な評価", "理由":"大吟醸なのに、味が人工アルコールのようになっており、偽物も流通しているので注意が必要と思われる。"},
    {"text": "早速今日付けてみましたが写真では、ブルーに見えていたのですが小さなガラス玉にしか見えずがっかりしました。取るとき留め金が壊れてしまい、留め金部分が小さすぎます。このような商品はこれから売るべきではありません。1度で壊れてしまい、腹が立って仕方ありません。買わなければ良かったと思っています。", "評価":"非常に不評", "理由":"ブルーに見えていたものが小さなガラス玉だった。また、取るときに留め金が壊れてしまいました。非常に壊れやすい状態で極めて不評である。"},
    {"text": "仕事中、スマホやカギなどの小物を入れて使用しています。今まではポケットタイプを使用していましたが、走ったりかがんだりした時に中身が飛び出すと困るため、いいものはないか探していました。2ジップタイプで、色はDカーキ。写真よりも少しだけ実物の方が濃く、良い色です。大きさもちょうど良く、邪魔になりません。ファスナーもそれぞれ逆方向から開くようになっており使いやすいです。スマホが正面に入れられるようになっており、取り出しやすくていいですよ。私はiPhone Xをハードタイプのケースに入れて使っていますが、測ったようにピッタリでした。500円とは思えない作りの良さです。気に入ったので、色違いを検討中です♪", "評価":"非常に高い評価 ", "理由":"2ジップタイプで、色も濃く良い色で、大きさもちょうどいいサイズで気に入った。上質な作りで500円とは思えない作りの良さだったため、スマホも取り出しやすく、快適に使えると思われた。"},
    {"text": "着心地はとても良く大変気に入りました。175/85の自分がきたサイズ感ですが1番大きいサイズを買いましたがダボダボにはなりませんでした。暑い時期も多いのでまだ活躍しそうです。", "評価":"非常に良い", "理由":"着心地がとても良く、暑い時期にも着る事が出来そうだから。"},
    {"text": "リビングで、使用する為に購入しました。他の方のレビューにあった通り、かなりコンパクトに郵送されてきました。組み立ては簡単で、すぐに使用できました。リモコンの電池が付属されていないので、あらかじめ、電池を用意されている方が良いかもしれません。", "評価":"非常に満足している", "理由":"組み立てが簡単で、、配送もコンパクトで到着したため。"},
    {"text": "実家の母の誕生日祝いとして贈りました。以前母の日で贈った際、とても気に入ってくれたので今回は誕生祝いで。やはり喜んでくれました！ナイフで軽くなぞるだけで切れる程、肉は非常に柔らかく塩胡椒だけで十分だそう。また、サイズも大きく食べ応えがあったと喜んでいました。ちなみに長さ25cm幅15cmが写真のステーキで、大皿じゃないとはみ出てしまったそうです！", "評価":"非常に良い ", "理由":"ナイフで軽くなぞるだけで切れるほど柔らかい肉、サイズも大きく食べ応えがあると喜んでいたことから、非常に良いと評価した"},
]

example_formatter_template4 = """
text: {text}
評価: {評価}\n
理由: {理由}\n
"""
example_prompt4 = PromptTemplate(
    template=example_formatter_template4,
    input_variables=["text", "評価", "理由"]
)

few_shot_prompt4 = FewShotPromptTemplate(
    examples=examples4,
    example_prompt=example_prompt4,
    prefix="入力された文章は商品に対するレビューである。この文章から商品に対する全体の評価、全体の評価に至った理由を生成して",
    suffix="text: {input}\n評価: \n理由:",
    input_variables=["input"],
    example_separator="\n\n",
)


# スクレイピングするURL
url = 'https://shopping.yahoo.co.jp/search?fr=shp-prop&ei=utf-8&p={keyword}'

def get_meta_property(url, property_name):
    # HTMLを取得
    response = requests.get(url)
    html = response.text
    
    # BeautifulSoupオブジェクトを作成
    soup = BeautifulSoup(html, 'html.parser')
    
    # meta要素を取得
    meta_tags = soup.find_all('meta', property=property_name)
    
    # meta要素のcontent属性を取得
    meta_contents = [tag.get('content') for tag in meta_tags]
    
    return meta_contents

#会話処理
log = ""
turn = 0
while input != "quit()":
    #会話ターンの計算
    turn += 1
    message = input ("🙋 Human: ")
    log += "🙋 Human:"+message +"\n"
    messages.append ({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        #model="gpt-4",
        messages=messages,
        temperature=0.8,
    )
    reply = response["choices"][0]["message"]["content"]
    prompt_text = few_shot_prompt.format(input=message)
    llm = OpenAI(model_name="gpt-3.5-turbo")
    #print(type(results))

    keyword = llm(prompt_text)
    keyword = keyword.replace(' ','')
    if keyword != "なし":
    #print(keyword))
        keyword = keyword.replace('keyword: ','')
        keyword = keyword.split(',')
        keyword_list += keyword
        keyword_sub = keyword

    if len(keyword_list) >0:
        str_list = ','.join(keyword_list)
        prompt_text2 = few_shot_prompt2.format(input=str_list)
        keyword2 = llm(prompt_text2)
        #print(prompt_text2)
        keyword2 = keyword2.replace('keyword: ','')
        keyword2 = keyword2.split(',')

    #何件の商品が存在するか検索
    name=[]
    re_try = 0
    if len(keyword2)>0:
        response = requests.get(url.format(keyword=keyword2))
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        print(soup)
        f = open("recommendation/chtest.txt","w")
        f.write(str(soup))
        f.close
        items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')

        try:
            name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
        #商品が存在しなかった場合の例外処理
        except AttributeError:
            print("先程の条件で検索を行いましたが商品が存在しなかった為，以下の条件で推薦を行います")
            #for item in keyword2:
            #    if item in keyword_sub:
            #        keyword2.remove(item)
            #print("aaaaaaaaaaa")
            #抽出した要素
            #print(keyword2)
            #除外する要素
            #print(keyword_sub)
            #print("bbbbbbbbbbb")
            keyword2 = [item.strip() for item in keyword2]
            keyword_sub = [item.strip() for item in keyword_sub]
            keyword2 = list(set(keyword2)-set(keyword_sub))
            #print(keyword2)
            research = ','.join(keyword2)
            print("条件："+research)   
            response = requests.get(url.format(keyword=research))
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            #print(soup)
            items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')
            #print(items)
            name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
            re_try = 1
        print(len(name))

    if (len(name)>0 and len(name)/2<10) or re_try == 1 or turn ==8:
        reply = "おすすめの商品を考えるので少々お待ちください"
        print("---\n🤖 Riley: " + reply + "\n---") 
        log += "🤖 Riley:" + reply + "\n"
        research = ','.join(keyword2)  
        print(keyword_list)
        print(research)
        response = requests.get(url.format(keyword=research))
        html = response.text
        #print(html)
        #f = open("yahoo.txt","w")
        #f.write(html)
        #f.close
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')
        name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
        #print(type(name))
        #print(len(name))
        #print(name)
        name_ls=[]
        name_ls2=[]
        short_name = []
        price_ls = []
        url_ls = []
        count = 0
        for n in name:
            if count % 2 == 0:
                #商品情報をlistに追加
                #print("name_ls")
                #print(count)
                #print(n.get_text(separator='/'))
                name_ls2 = (n.get_text(separator='/')).split('/')
                #print(name_ls2[0])
                #print(name_ls2[1]+name_ls2[2])
                #print("-------")
                #print(n.text)
                name_ls.append(name_ls2[0])
                #name_ls.append(n.text)
                #商品情報を紹介する時用に加工
                prompt_text3 = few_shot_prompt3.format(input=n.text)
                shortname = llm(prompt_text3)
                #加工した商品情報をlistに追加
                short_name.append(shortname)
            else:
                #print("price_ls")
                #print(count)
                #print(n.text)
                price_ls.append(name_ls2[1]+name_ls2[2])
                #price_ls.append(n.text)
            count += 1
        item_info = []
        #urlを取得
        for u in name:
            if count %2 == 0:
                url_ls.append(u['href'])
            count += 1
        #商品情報、価格、urlを格納
        for N, P, U, SN in zip(name_ls, price_ls, url_ls, short_name):
            item_info.append((N,P,U,SN))
        #print("name"+str(len(name_ls)))
        #print("price"+str(len(price_ls)))
        #print("url"+str(len(url_ls)))
        #print("Sname"+str(len(short_name)))

        #pprint(item_info)

        df_info = pd.DataFrame({'name':name_ls,
                                'price':price_ls,
                                'url':url_ls,
                                'Sname':short_name})
        #print(df_info)
        #各URLから店名を取得
        shop_name = []
        shop_review = []
        for col in range(len(df_info)):
            d_url = df_info.loc[col,'url']
            d_response = requests.get(d_url)
            d_html = d_response.text
            d_shop = BeautifulSoup(d_html, 'html.parser') 
            property_name = 'twitter:data2'
            meta_data = get_meta_property(d_url, property_name)
            shop_name.append(meta_data)
            #以下より商品のレビューを取得
            review = d_shop.find_all('p', class_ ='elItemCommentText')
            shop_review.append(review)
        df_info['shops_name'] = shop_name
        df_info['reviews'] = shop_review
        #print(df_info.loc[0,'name'])
        df_info.to_csv('to_csv_out3.csv')
        #推薦する商品を選択
        if len(name)/2>3:
            df_info =df_info.sample(n=3)
            #print(df_info)
            df_info.index = ['0','1','2']
            #print(type(df_info))
            #print(df_info)
            #print(df_info.shape)
        merchandise = []
        rows_list = df_info.values.tolist()
        number = 0
        goods = ""
        #print("rows_list")
        #print(rows_list)
        candidate = ""
        for row in rows_list:
            #print(row)
            #print(type(row))
            #print(len(row))
            name = df_info.at[str(number),'Sname']
            shop = str(df_info.at[str(number),'shops_name'])
            price =df_info.at[str(number),'price']
            url = df_info.at[str(number),'url']
            number += 1
            print("商品" + str(number) + ":"+ shop + "の" + name)
            candidate += "商品" + str(number) + ":"+ shop + "の" + name + "\n"
            rows = ','.join(map(str,row))
            #評価とその評価理由をレビュー文から生成
            if len(row[5])>0:
                text = random.choice(row[5])
                print(text)
                prompt_text = few_shot_prompt4.format(input=text)
                #llm = ChatOpenAI(temperature=0, model_name='gpt-4')
                llm = OpenAI(model_name="gpt-4")
                #llm = OpenAI(model_name="text-davinci-003")
                print("///////////////////")
                print(llm(prompt_text))
                print("///////////////////")
                rev = llm(prompt_text)
                merchandise = ("商品" + str(number) + ":" + shop + "の" + name +"価格:"+ price +"URL:"+url+"評価："+ rev +"\n")
            else:
                merchandise = ("商品" + str(number) + ":" + shop + "の" + name +"価格:"+ price +"URL:"+url+"\n")
            goods += merchandise
            #print(goods)
        break
    else :
        messages.append({"role": "assistant", "content": reply})
        print("---\n🤖 Riley: " + reply + "\n---")
        log += "🤖 Riley:" + reply + "\n"
    print(keyword_list)
    print(keyword2)
print(goods)

#今までの会話を一度要約
#一度プロンプトを初期化
openai.api_key = ''
messages.clear()
system_msg = "会話の内容を要約して"
messages.append({"role": "system", "content": system_msg})
message = log
messages.append ({"role": "user", "content": message})
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    temperature=0.8,
)
reply = response["choices"][0]["message"]["content"]
#log = reply
print("############")
print(reply)
print("############")


#商品決定後の会話
#一度プロンプトを初期化
messages.clear()
system_msg = "以下の条件で商品を推薦するシステム,\
1.推薦する商品はプロンプトにある商品のみ,\
2.会話は簡潔に,\
3.商品を推薦する時は推薦する理由も明確に,\
4.ユーザが購買する商品を決定したら対象の商品のURLを表示,\
5.ユーザがプロンプトにない商品を求めた場合は再検索をするように促して"
messages.append({"role": "system", "content": system_msg})
messages.append({"role": "system", "content": goods})
messages.append({"role": "system", "content": log})
#logに記録されていない会話を追加
print("お待たせいたしました。貴方におすすめの商品は以下の通りです。")
log += "お待たせいたしました。貴方におすすめの商品は以下の通りです。\n"
print(candidate)
log += candidate
while input != "quit()":
    message = input ("🙋 Human: ")
    log += "🙋 Human: " + message + "\n"
    if message == "終了":
        ld = open("/recommendation/log_3.txt","a")
        ld.write("-------------------------------------------")
        ld.write(log)
        ld.close
        break
    messages.append ({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.8,
    )

    reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": reply})
    print("---\n🤖 Riley: " + reply + "\n---")
    log += "🤖 Riley: " + reply + "\n"
    #これまでの会話を表示
    #print(log)

