#ver30
#別の商品を推薦するには実験用の設定を削除してください
#systemに毎ターン総検索数と検索結果を与えて、推薦のタイミングの参考とさせる
#検索の際値段に関する内容から適切なURLを生成できるようにする
#システム概要
#システムとユーザが会話を行い、商品推薦を行うシステム
#商品推薦時には、評価のみを提示する.
import openai
import os
#from langchain import PromptTemplate
from langchain import FewShotPromptTemplate
#from langchain.llms import OpenAI
#from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
#from langchain.llms import OpenAI
#from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import OpenAI
from langchain.output_parsers import PydanticOutputParser,OutputFixingParser
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
import random
import re
import json
import ast

# Assign OpenAI API Key from environment variable
openai.organization = ""
openai.api_key = ''
os.environ['OPENAI_API_KEY'] = ''
messages = []
keyword_sublist = []
keyword2 = []
name=[]

# スクレイピングするURL
#url = 'https://shopping.yahoo.co.jp/search?fr=shp-prop&ei=utf-8&p={keyword}'
url = 'https://shopping.yahoo.co.jp/search?pf={BottomPlice}&pt={TopPlice}&fr=shp-prop&ei=utf-8&p={keyword}'
"""
system_msg = "あなたは「ユーザに対して推薦する商品の条件を聞くシステム」です,\
以下の8つのルールに沿って会話を進めてください,\
1.最初にユーザがどのような商品を求めているか聞く,\
2.「検索件数」を絞るための質問を「各商品の情報」から考えて（ただし選択肢を与えて選ばせるのは禁止）.\
3.性別によって求める商品が一般的に異なる（服など）をユーザが求めている場合はその情報も聞いて.\
4.「検索件数」をある程度絞りきれたと判断した時のみ推薦を行える。\
5.推薦や商品の紹介を行う際は必ずプロンプト内の関数を使用すること.\
6.この会話で商品を紹介することは禁止.\
7.「各商品の情報」は質問を考える以外での使用は禁止.\
8.ユーザに「各商品の情報」を提示するのは禁止"
"""
system_msg = "あなたは「ユーザに対して推薦する商品の条件を聞くシステム」です,\
以下の基本ルールと推薦タイミングに関するルール、禁止行為を守って会話を進めてください,\
基本ルール：\
1.最初にユーザがどのような商品を求めているか聞く,\
2.プロンプト内の「検索件数」を絞るための質問を「各商品の情報」から考えて（ただし選択肢を与えて選ばせるのは禁止）.\
3.ユーザが例を求めるような質問をしてきたら、例を提示して\
4.性別や歳によって求める商品が一般的に異なる（服など）をユーザが求めている場合はその情報も聞いて.\
推薦タイミングに関するルール\
1.「検索件数」をある程度に絞りきれた時のみ推薦を行える。\
2.「検索件数」が絞りきれても、文脈上ユーザが質問をしている場合は質問に答えてから推薦を行って\
その他禁止行為：\
1.「検索件数」を絞るために選択肢を提示してその中から選ばせる事は禁止.\
2.この会話で商品を紹介することは禁止.\
3.「各商品の情報」は質問を考える以外での使用は禁止."

system_msg2 = "あなたは「推薦した商品をユーザに説明するシステム」です,\
以下の4つのルールに沿って会話を進めてください,\
1.会話は簡潔に,\
2.商品を説明する時はプロンプト内にある「評価」と「評価の理由」、以下で定義する「ユーザに適している理由」を例のように箇条書きではなくべた書きで提示して,\
「ユーザに適している理由」：商品がユーザにとってどのような点で適しているか（ユーザに関する情報から生成して）,\
3.推薦する商品に対してはでいるだけ好意的に,\
4.ユーザが商品に納得していない場合、別の商品を推薦する為に「ユーザに対して推薦する商品の条件を聞くシステム」に切り替えて"


#実験用商品設定
shop1 = "野中精肉店"
name1 = "佐賀牛ワサビで食べる牛肉もも肉ステーキ100グラム"
info1 = "佐賀牛 わさびで食べるステーキ 牛肉 牛モモ肉ステーキ 100g"
price1 = "1560円"
url1 = "https://store.shopping.yahoo.co.jp/nonaka29/012-04.html"
rev1 = "評価：非常に高評価,評価の理由：リーズナブルな値段かつ柔らかく美味しいため"
merchandise1 = ("商品:" + shop1 + "の" + name1 +"価格:"+ price1 + "商品概要："+ info1 +"URL:"+url1+ rev1 +"\n")

shop2 = "アイリスオーヤマ"
name2 = "冷凍冷蔵庫 87リットル PRC-B092D"
info2 = "冷蔵庫 冷凍庫 87L 一人暮らし 小型 家庭用 小型冷蔵庫 ミニ冷蔵庫 アイリスオーヤマ 冷凍 2ドア コンパクト 冷凍冷蔵庫 87リットル PRC-B092D [AR対応]"
price2 = "22199円"
url2 = "https://store.shopping.yahoo.co.jp/insdenki-y/p7155749.html?sc_i=shopping-pc-web-top--reco1-item"
rev2 = "評価：非常に高評価,評価の理由：コスパの良さ、迅速な配送、使いやすさ、清潔感のあるデザインが高水準なため"
merchandise2 = ("商品:" + shop2 + "の" + name2 +"価格:"+ price2 + "商品概要："+ info2 +"URL:"+url2+ rev2 +"\n")

shop3 = "RAFFRULE"
name3 = "半袖 吸汗 速乾のメンズパーカー"
info3 = "パーカー メンズ スタンド 半袖 吸汗 速乾 ドライ ストレッチ 無地 ジップパーカー 薄手 夏 スポーツ アウトドア お揃い イベント【15A0001】送料無料 通販M3"
price3 = "1798円"
url3 = "https://store.shopping.yahoo.co.jp/limited/15a0001.html"
rev3 = "評価：非常に高評価,評価の理由：この商品は、軽量で通気性が良く、実用的なデザインと速乾性を兼ね備えた高コスパの半袖パーカ>ーのため"
merchandise3 = ("商品:" + shop3 + "の" + name3 +"価格:"+ price3 + "商品概要："+ info2+"URL:"+ url3+ rev3 +"\n")


#各ターンで検索クエリを推定する関数
def estimation_query(log):
    # カンマで区切られたリストを解析するパーサーを初期化する
    output_parser = CommaSeparatedListOutputParser()

    # パーサーのフォーマット命令を取得する
    format_instructions = output_parser.get_format_instructions()

    # 特定のトピックに関するカンマで区切られたリストを生成するためのプロンプトテンプレートを定義する
    prompt = PromptTemplate(
        template="会話の内容から「Human」が求めている商品の検索するためのクエリを「リスト」にして（クエリは可能な限り単語毎に分割し、かつ検索に不要な物と値段に関する情報は除外して）。会話内容：{subject}。ただし会話内に参考となる情報が無い場合はなしと出力して\n{format_instructions}",
        input_variables=["subject"],
        partial_variables={"format_instructions": format_instructions}
    )
    # OpenAIモデルを初期化する。温度は0に設定（生成される答えはより確定的で、ランダム性が少ない）
    model = OpenAI(model_name="gpt-4o",temperature=0.0)
    # プロンプトをフォーマットする。
    _input = prompt.format(subject= log)
    # モデルを使用して出力を生成する
    output = model(_input)
    # パーサーを使用して出力を解析する
    turn_query = output_parser.parse(output)
    return turn_query

#検索クエリからユーザの希望価格（最低価格、最高価格、希望価格等を取り出す）
def price_query(log):
    # Pydanticで型を定義する
    class serchplice(BaseModel):
        TopPlice: int = Field(description="上限価格")
        BottomPlice: int = Field(description="最低価格")
        SuggestedPlice: int = Field(description="どちらともいえない希望価格")
    # OutputParserを用意する
    parser = PydanticOutputParser(pydantic_object=serchplice)
    # OutputFixingParserでPydanticOutputParserをラップする
    output_fixing_parser = OutputFixingParser.from_llm(
        parser=parser,
        llm=ChatOpenAI(model_name="gpt-4o",temperature=0.0)
    )
    # プロンプトを作成
    prompt_template = PromptTemplate(
        template="ユーザが希望している価格帯を抽出して。会話内容：{subject}。価格に関する情報が無い項目は0と出力。~千や万等の漢字表記は数字に変換して出力\n{format_instructions}\n",
        input_variables=["subject"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    prompt = prompt_template.format_prompt(subject=log)
    #　モデルを用意
    model = OpenAI(model_name="gpt-4o",temperature=0.0)
    # 応答を得る
    output = model(prompt.to_string())
    # OutputFixingParserでパースする
    outoput = output_fixing_parser.parse(output)
    # 応答を構文解析
    pricequery = parser.parse(output)
    return pricequery

#検索ワードから何件の検索結果があったか調べる関数
def number_of_searches(Plice,url,query):
    name=[]
    test = url.format(BottomPlice=" ",TopPlice=" ",keyword=query)
    print(test)
    response = requests.get(url.format(BottomPlice=" ",TopPlice=" ",keyword=query))
    if Plice['TopPlice'] != str(0):
        print(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
    if Plice['BottomPlice'] != str(0):
        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
    if Plice['SuggestedPlice'] != str(0):
        print(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
    if Plice['BottomPlice'] != str(0) and Plice['TopPlice'] != str(0):
        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
    if Plice['BottomPlice'] != str(0) and Plice['SuggestedPlice'] != str(0):
        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))

    query = query.split()
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')
    try:
        name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
    except AttributeError:
        name = []
        nnos = 0
    nnos = len(name)
    return name,nnos,items

#各ターンで検索を行い検索結果をまとめる(値段,商品情報)
def Search_for_each_turn(items):
    try:
        #値段を抽出
        price_ls = items.find_all('span', class_='SearchResultItemPrice_SearchResultItemPrice__value__G8pQV')
        price_ls = [x.text for x in price_ls]
        #商品に関する情報
        name_ls = items.find_all('span', class_='SearchResultItemTitle_SearchResultItemTitle__name__BwTpC')
        name_ls = [x.text for x in name_ls]
        #print("商品情報"+str(len(name_ls)))
        #print(name_ls)
        #print(len(name_ls))
        #print("値段"+str(len(price_ls)))
        #print(price_ls)
        #print(len(price_ls))
        df_info = pd.DataFrame({'商品情報':name_ls,
                                '値段':price_ls})
    except AttributeError:
        df_info = pd.DataFrame()
        name_ls = []
    return df_info,name_ls

#会話内容を要約する関数
def summary(log):
    messages.clear()
    system_msg = "会話の内容からユーザに関する情報をまとめて"
    messages.append({"role": "system", "content": system_msg})
    message = log
    messages.append ({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.8,
    )
    reply_log = response["choices"][0]["message"]["content"]
    print("############")
    print(reply_log)
    print("############")
    return reply_log

#推薦する際のアイテムを検索し情報をまとめる関数
def recommed(Plice,name,nnos,items,df_info,url,name_ls,log,query):
    #何件の商品が存在するか検索
    test = url.format(BottomPlice=" ",TopPlice=" ",keyword=query)
    print(test)
    response = requests.get(url.format(BottomPlice=" ",TopPlice=" ",keyword=query))
    if Plice['TopPlice'] != str(0):
        print(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
    if Plice['BottomPlice'] != str(0):
        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
    if Plice['SuggestedPlice'] != str(0):
        print(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
    if Plice['BottomPlice'] != str(0) and Plice['TopPlice'] != str(0):
        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
    if Plice['BottomPlice'] != str(0) and Plice['SuggestedPlice'] != str(0):
        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))
        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))

    query = query.split()
    print(query)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    if nnos==0:
        items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')
        try:
            print("以下の条件で一度商品を考えます")
            log += "🤖 Riley:" + "以下の条件で一度商品を考えます" + "\n"   
            research = ','.join(query)
            print("条件："+research)   
            name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
        except AttributeError:
            print("申し訳ありません、該当する商品が見つかりませんでした。条件を緩和しておすすめの商品を考えてみます")
            log += "🤖 Riley:" + "申し訳ありません、該当する商品が見つかりませんでした。条件を緩和しておすすめの商品を考えてみます" + "\n"   
            while True:
                query = query[:-1]
                query = ','.join(query)
                test = url.format(BottomPlice=" ",TopPlice=" ",keyword=query)
                print(test)
                response = requests.get(url.format(BottomPlice=" ",TopPlice=" ",keyword=query))
                try:
                    if Plice['TopPlice'] != str(0):
                        print(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
                        response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
                    if Plice['BottomPlice'] != str(0):
                        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
                        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
                    if Plice['SuggestedPlice'] != str(0):
                        print(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
                        response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
                    if Plice['BottomPlice'] != str(0) and Plice['TopPlice'] != str(0):
                        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
                        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
                    if Plice['BottomPlice'] != str(0) and Plice['SuggestedPlice'] != str(0):
                        print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))
                        response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))
                    html = response.text
                    soup = BeautifulSoup(html, 'html.parser')
                    items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')
                    name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
                    print("商品の確認ができました。以下が最終的な条件です")
                    print("条件："+research)
                    log += "🤖 Riley:" + "商品の確認ができました。以下が最終的な条件です" + "\n"
                    log += "🤖 Riley:" + "条件："+research + "\n"   
                    break
                except AttributeError:
                    print("検索中です")
                    query = query.split(",")
        print("numnumnumnumnumnumnumnum")
        print(len(name))
        print("numnumnumnumnumnumnumnum")
        reply = "おすすめの商品を考えるので少々お待ちください"
        print("---\n🤖 Riley: " + reply + "\n---") 
        log += "🤖 Riley:" + reply + "\n"
        query = ','.join(query)  
        test = url.format(BottomPlice=" ",TopPlice=" ",keyword=query)
        print(test)
        response = requests.get(url.format(BottomPlice=" ",TopPlice=" ",keyword=query))
        if Plice['TopPlice'] != str(0):
            print(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
            response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['TopPlice'],keyword=query))
        if Plice['BottomPlice'] != str(0):
            print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
            response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=" ",keyword=query))
        if Plice['SuggestedPlice'] != str(0):
            print(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
            response = requests.get(url.format(BottomPlice=" ",TopPlice=Plice['SuggestedPlice'],keyword=query))
        if Plice['BottomPlice'] != str(0) and Plice['TopPlice'] != str(0):
            print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
            response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['TopPlice'],keyword=query))
        if Plice['BottomPlice'] != str(0) and Plice['SuggestedPlice'] != str(0):
            print(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))
            response = requests.get(url.format(BottomPlice=Plice['BottomPlice'],TopPlice=Plice['SuggestedPlice'],keyword=query))
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        #items = soup.find('li', class_='SearchResults_SearchResults__page__OJhQP')
        #name = items.find_all('a', class_='SearchResult_SearchResult__detailsContainerLink__HrJQL')
        df_info,name_ls = Search_for_each_turn(items)
    short_name = []
    count = 0
    llm = OpenAI(model_name="gpt-4o")
    for n in name_ls:
        prompt_text3 = few_shot_prompt3.format(input=n)
        shortname = llm(prompt_text3)
        #加工した商品情報をlistに追加
        short_name.append(shortname)
        count += 1
    #print("商品名"+str(len(short_name)))
    #print(name)
    url_ls = [a['href'] for a in name]
    #print(url_ls)
    #print(len(url_ls))
    df_info['url'] = url_ls
    df_info['商品名'] = short_name
    #各URLから店名を取得
    shop_name = []
    shop_review = []
    for col in range(len(df_info)):
        d_url = df_info.loc[col,'url']
        d_response = requests.get(d_url)
        d_html = d_response.text
        d_shop = BeautifulSoup(d_html, 'html.parser') 
        shopN = d_shop.find("p",class_="styles_storeName__uYedP")
        #print(shopN.get_text())
        shop_name.append(shopN.get_text())
        #以下より商品のレビューを取得
        #review = d_shop.find_all('p', class_ ='elItemCommentText')
        review_tag = d_shop.find_all(class_ ='styles_body___v6TF')
        review = [xrev.text for xrev in review_tag]
        shop_review.append(review)

    #レビューデバック用
    #print("d_re,d_re,d_re,d_re,d_re,d_re,d_re")
    d_d_url = "https://store.shopping.yahoo.co.jp/matador/sankan.html"
    d_d_response = requests.get(d_d_url)
    d_d_html = d_d_response.text
    d_d_shop = BeautifulSoup(d_d_html, 'html.parser')
    #d_review = d_d_shop.find_all('p', class_ ='Review__starWrapper')
    d_review = d_d_shop.find_all(class_ ='styles_body___v6TF')
    rev_list = [xr.text for xr in d_review]
    #print(rev_list)
    d_ref = open("d_reviews.txt","w")
    d_ref.write(str(d_d_shop))
    d_ref.close
    #print("d_re,d_re,d_re,d_re,d_re,d_re,d_re")

    df_info['店名'] = shop_name
    df_info['商品レビュー'] = shop_review
    df_info.to_csv('to_csv_out2.csv')
    print("||||||||||||||||||||||||")
    print(df_info['商品レビュー'])       
    df_info['商品レビュー'] = df_info['商品レビュー'].apply(lambda x: 'NaN' if x == [] else x)
    df_info_select = df_info[df_info['商品レビュー'].str.endswith('e', na=True)]
    #print(df_info_select['商品レビュー'])
    #print(df_info_select.shape[0])
    print("||||||||||||||||||||||||")
    #推薦する商品を選択
    #まずレビューを含むデータがあるか判定
    if df_info_select.shape[0]>3:
        df_info = df_info_select.sample(n=3)
    elif 3>df_info_select.shape[0]>0:
        df_info = df_info_select
    elif df_info.shape[0]>3:
        df_info = df_info.sample(n=3)
        print("レビュー文含む商品無し")
        log += "🤖 Riley:" + "レビュー文含む商品無し" + "\n"
    else:
        df_info = df_info
        print("レビュー文含む商品無し")
        log += "🤖 Riley:" + "レビュー文含む商品無し" + "\n"
    df_info = df_info.reset_index(drop=True)
    merchandise = []
    rows_list = df_info.values.tolist()
    number = 0
    goods = ""
    candidate = ""
    print(df_info)
    for row in rows_list:
        try:
            name = df_info.at[str(number),'商品名']
        except KeyError:
            name = df_info.at[number,'商品名']               
        try:
            shop = str(df_info.at[str(number),'店名'])
        except KeyError:
            shop = str(df_info.at[number,'店名'])
        try:
            price =df_info.at[str(number),'値段']
        except KeyError:
            price =df_info.at[number,'値段']
        try:
            url = df_info.at[str(number),'url']
        except KeyError:
            url = df_info.at[number,'url']
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
            llm = OpenAI(model_name="gpt-4o")
            #llm = OpenAI(model_name="text-davinci-003")
            print("///////////////////")
            print(llm(prompt_text))
            print("///////////////////")
            rev = llm(prompt_text)
            merchandise = ("商品" + str(number) + ":" + shop + "の" + name +"価格:"+ price +"URL:"+url+"評価："+ rev +"\n")
        else:
            merchandise = ("商品" + str(number) + ":" + shop + "の" + name +"価格:"+ price +"URL:"+url+"\n")
        goods += merchandise
    return goods,candidate

#プロンプト１と２を切り替えるための準備を行う関数
#おすすめした商品とユーザがどのような点を不満に思っているのかまとめた内容を格納（プロンプト１に情報を渡すため）
def reconsider(log,resreco):
    reply_log = summary(log)
    return reply_log

#ユーザに対して商品の説明をする関数
def explanation(goods,log,system_msg2,candidate,messages):
    #実験用商品再設定（実験以外では下2行を削除）
    #goods = merchandise1
    #candidate = "商品:"+ shop1 + "の" + name1 + "\n"
    #今までの会話を一度要約
    reply_log = summary(log)
    #商品決定後の会話
    #一度プロンプトを初期化
    messages.clear()
    messages.append({"role": "system", "content": system_msg2})
    messages.append({"role": "system", "content": goods})
    messages.append({"role": "system", "content": reply_log})

    #logに記録されていない会話を追加
    print("お待たせいたしました。貴方におすすめの商品は以下の通りです。")
    log += "お待たせいたしました。貴方におすすめの商品は以下の通りです。\n"
    print(candidate)
    log += candidate

    while input != "quit()":
        message = input ("🙋 Human: ")
        log += "🙋 Human: " + message + "\n"
        if message == "終了":
            ld = open("log_1.txt","a")
            ld.write("-------------------------------------------")
            ld.write(log)
            ld.close
            break

        messages.append ({"role": "user", "content": message})
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.8,
            functions = my_function2,
            function_call = "auto",
        )

        reply = response["choices"][0]["message"]["content"]
        reply2 = response["choices"][0]["message"]
        messages.append({"role": "assistant", "content": reply})
        #再検索をするための処理
        if reply2.get("function_call"):
            print("再検索の為、プロンプトを１に切り替え")
            arguments = reply2["function_call"]["arguments"]
            resreco = json.loads(arguments).get("Reference_info")
            print(resreco)
            function_response2 = reconsider(log,resreco)
            action = "switching"
            break

        else:
            print("---\n🤖 Riley: " + reply + "\n---")
            log += "🤖 Riley: " + reply + "\n"
    return action,function_response2,log,message

my_function1 = [
    {   
        #関数名
        "name": "recommed",
        #関数の説明
        "description": "商品の推薦や商品の詳細を説明するための関数。",
        #関数の引数の定義
        "parameters": {
            "type": "object",
            "properties": {
                "select": {
                    "type": "string", 
                    "description": f"商品を検索するための検索クエリ（出来るだけ詳細に、かつクエリは可能な限り細かく分割）",
                },
            },
            "required": ["select"]
        }
    }]
my_function2 = [
    {
        "name": "reconsider",
        #関数の説明
        "description": "「ユーザに対して推薦する商品の条件を聞く」システムに切り替える為の関数",
        #関数の引数の定義
        "parameters": {
            "type": "object",
            "properties": {
                "Reference_info": {
                    "type": "string", 
                    "description": f"ユーザが求めている商品の情報、推薦した商品、ユーザ反応（不満点等）をまとめた内容",
                },
            },
            "required": ["Reference_info"]
        }
    }
]

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
    {"text": "生地が恐ろしく薄い。1,000円のＹシャツよりも薄い。一度洗濯すると恐ろしくシワシワ。とても5,000円の価値があるとは思えない。殿堂入り商品とあるが、本当なのだろうか？。", "評価":"非常に不満"},
    {"text": "普段ゲームをあまりしませんがかなりの時間をやり込みました。無双なのでひたすらアクションではありますが、ストーリーを進めることができ、前作とのつながりが分かるので非常に面白かったです。ただ前作ほどの新鮮感はやはり無いですね。", "評価":"非常に面白い"},
    {"text": "すごくコンパクトなのに普通のエコバッグより大きめでたくさん荷物が入ります。想像以上かも。それが3つも届いてこの価格はありがたい", "評価":"大変高い評価"},
    {"text": "初めは文字盤40ミリ大きく感じましたが、日付の文字も見やすいのでとても使いやすいです。グレーを一度注文しようとした時に品切れでしたが、日を改めてサイトを見たときに在庫になっていたので即注文しました。服にも合わせやすい色なので助かっています。", "評価":"高評価"},
    {"text": "すぐはきつぶしてしまうので、購入しました。色合いも想像通りでサイズ感もいいです。また、見た目だけではなく歩きやすく疲れづらいような気がしてます。ビジネスシューズは割とすぐ買うことが多いので、こちらおすすめさせていただきます。", "評価":"高評価 "},
    {"text": "実家への贈答品として送り、今回、帰省した際に飲ませてもらいました。獺祭は、よく購入して飲んでいますが、こんなまずいのは初めてです。大吟醸なのに、人工アルコールのような味が・・・非常に残念です。販売店は悪くないのかもしれませんが、最近は流通ルートに偽物も流れていると聞きますので、注意された方が良いと思います。", "評価":"非常に残念な評価"},
    {"text": "早速今日付けてみましたが写真では、ブルーに見えていたのですが小さなガラス玉にしか見えずがっかりしました。取るとき留め金が壊れてしまい、留め金部分が小さすぎます。このような商品はこれから売るべきではありません。1度で壊れてしまい、腹が立って仕方ありません。買わなければ良かったと思っています。", "評価":"非常に不評"},
    {"text": "仕事中、スマホやカギなどの小物を入れて使用しています。今まではポケットタイプを使用していましたが、走ったりかがんだりした時に中身が飛び出すと困るため、いいものはないか探していました。2ジップタイプで、色はDカーキ。写真よりも少しだけ実物の方が濃く、良い色です。大きさもちょうど良く、邪魔になりません。ファスナーもそれぞれ逆方向から開くようになっており使いやすいです。スマホが正面に入れられるようになっており、取り出しやすくていいですよ。私はiPhone Xをハードタイプのケースに入れて使っていますが、測ったようにピッタリでした。500円とは思えない作りの良さです。気に入ったので、色違いを検討中です♪", "評価":"非常に高い評価 "},
    {"text": "着心地はとても良く大変気に入りました。175/85の自分がきたサイズ感ですが1番大きいサイズを買いましたがダボダボにはなりませんでした。暑い時期も多いのでまだ活躍しそうです。", "評価":"非常に良い"},
    {"text": "リビングで、使用する為に購入しました。他の方のレビューにあった通り、かなりコンパクトに郵送されてきました。組み立ては簡単で、すぐに使用できました。リモコンの電池が付属されていないので、あらかじめ、電池を用意されている方が良いかもしれません。", "評価":"非常に満足している"},
    {"text": "実家の母の誕生日祝いとして贈りました。以前母の日で贈った際、とても気に入ってくれたので今回は誕生祝いで。やはり喜んでくれました！ナイフで軽くなぞるだけで切れる程、肉は非常に柔らかく塩胡椒だけで十分だそう。また、サイズも大きく食べ応えがあったと喜んでいました。ちなみに長さ25cm幅15cmが写真のステーキで、大皿じゃないとはみ出てしまったそうです！", "評価":"非常に良い"},
]

example_formatter_template4 = """
text: {text}
評価: {評価}\n
"""
example_prompt4 = PromptTemplate(
    template=example_formatter_template4,
    input_variables=["text", "評価"]
)

few_shot_prompt4 = FewShotPromptTemplate(
    examples=examples4,
    example_prompt=example_prompt4,
    prefix="入力された文章は商品に対するレビューである。この文章から商品に対する全体の評価を生成して",
    suffix="text: {input}\n評価:",
    input_variables=["input"],
    example_separator="\n\n",
)

#会話処理
log = ""
turn = 0

messages.append({"role": "system", "content": system_msg})
print("Say hello to your new assistant!")

while input != "quit()":
    #会話ターンの計算
    turn += 1
    message = input ("🙋 Human: ")
    log += "🙋 Human:"+message +"\n"
    messages.append ({"role": "user", "content": message})
    #prompt_text = few_shot_prompt.format(input=message)
    #llm = OpenAI(model_name="gpt-3.5-turbo")

    #keyword = llm(prompt_text)
    equery_list = estimation_query(log)
    Plice = price_query(log)
    #print(type(Plice))
    print(Plice)
    #langchainのJson形式の出力がよくわからなかったのでとりあえず辞書型に変換
    Plice = dict(item.split('=') for item in str(Plice).split())
    if len(equery_list) >0 and equery_list[0] != "なし":
        print(equery_list)
        equery = [str(i) for i in equery_list]
        equery = " ".join(equery)
        name,nnos,items = number_of_searches(Plice,url,query=equery)
        print(nnos)
        df_info,name_ls = Search_for_each_turn(items)
        Tdf_info = df_info.to_string(header=True, index=True, index_names=True)
        print(df_info)
        messages.append({"role": "system", "content": "検索件数"+ str(nnos) +"件"})
        messages.append({"role": "system", "content": "各商品の情報"+Tdf_info}) 

    response1 = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.8,
        functions = my_function1,
        function_call = "auto",
    )

    reply = response1["choices"][0]["message"]["content"]
    reply2 = response1["choices"][0]["message"]

    if reply2.get("function_call"):
        print("function_call,function_call,function_call,function_call,function_call,function_call,")
        function_name = reply2["function_call"]["name"]
        arguments = reply2["function_call"]["arguments"]
        resreco = json.loads(arguments).get("select")
        print(resreco)
        #resreco = [str(i) for i in resreco]
        #resreco = " ".join(resreco)
        function_response,candidate = recommed(Plice,name,nnos,items,df_info,url,name_ls,log,query=resreco)
        goods = function_response
        action,function_response2,log,message = explanation(goods,log,system_msg2,candidate,messages)
        if action == "switching":
            messages.clear()
            system_msg = system_msg + "追加指示：再度推薦を行う為に、ユーザに推薦の為の条件を聞き出して"
            messages.append({"role": "system", "content": system_msg})
            messages.append({"role": "system", "content": log})
            print(function_response2)
            messages.append({"role": "system", "content": function_response2})
            messages.append({"role": "user", "content": message})
            response1 = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.8,
                functions = my_function1,
                function_call = "auto",
            )
            reply = response1["choices"][0]["message"]["content"]
            reply2 = response1["choices"][0]["message"]            
            #print("%&%&%&%&%&%&%&%&%&%&%&%&")
            #print(reply)
            #print(type(reply))
            #print(reply2)
            #print("%&%&%&%&%&%&%&%&%&%&%&%&")
            messages.append({"role": "assistant", "content": reply})
            print("---\n🤖 Riley: " + reply + "\n---")
            log += "🤖 Riley:" + reply + "\n"

    else :
        messages.append({"role": "assistant", "content": reply})
        print("---\n🤖 Riley: " + reply + "\n---")
        log += "🤖 Riley:" + reply + "\n"
    print(equery_list)
print(goods)