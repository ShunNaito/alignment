#!/usr/bin/python
#coding:utf-8

import os, cgi, csv, sys, codecs, MeCab

if 'QUERY_STRING' in os.environ:
    query = cgi.parse_qs(os.environ['QUERY_STRING'])
else:
    query = {}

#時系列データの日付が飛んでる場合はcsvの方で補完しておく

file_name = './CSVdata'

date = [] #助数詞のみを格納(中旬,初頭なども格納)
num = [] #数字部分を格納(□旬='-1',初頭='-2'を格納)

data_original = [] #ハイフン付きで時系列データ格納(8-01, 100.0)
data = [] #ハイフンなし時系列データの格納(801, 100.0)

f = open('text.txt') #テキストファイルの読み込み
mecab = MeCab.Tagger("-Ochasen  -u usrdic.dic")
text = f.read() #変数に格納
f.close()

node = mecab.parseToNode(text).next #形態素解析結果を双方向に格納


#日付の抽出
p_year = "0"
p_month = "0"
#p_day = "0"
p_kikan = "旬"
#p_zengo = "前後半"
p_hendo = 0 #変動の表現 -1=減少, 1=増加

while node:
	if node.feature.split(",")[2] == "助数詞": #月日を数詞と助数詞に分けて判断
		if node.surface == "月": #日判断
			date.append(node.surface)
			num.append(node.prev.surface)
			p_month = int(node.prev.surface)
			#print p_month #抽出した月の確認用

		elif node.surface == "年": #年判断
			date.append(node.surface)
			num.append(node.prev.surface)
			p_year = int(node.prev.surface)
			#print p_year #抽出した年の確認用

	elif node.surface == "上旬" or node.surface == "中旬" or node.surface == "下旬": #期間表現1
		date.append(node.surface)
		num.append('-1')
		p_kikan = str(node.surface)
		#print p_kikan #抽出した日付表現の確認用

	elif node.surface == "初頭" or node.surface == "末": #期間表現2
		date.append(node.surface)
		num.append('-2')
		p_kikan = str(node.surface)
		#print p_kikan #抽出した日付表現の確認用


	node = node.next

#for i in range(0,len(num)): #日付に関する抽出確認(テスト用)
#	print num[i],date[i]


node = mecab.parseToNode(text).next #nodeを先頭に戻す

#グラフプリミティブの抽出
#グラフプリミティブの語はテキストファイルに保存して管理している。前半ではそれを読み込み変数に格納している
p_graphword = "" #グラフプリミティブを指す単語を格納

josho = []
kako = []

d = open('DataSet/up.txt') #グラフ形状"/"に関する単語ファイルを格納
for line in d.readlines():
	josho.append(line.rstrip())
d = open('DataSet/down.txt') #グラフ形状"\"に関する単語ファイルを格納
for line in d.readlines():
	kako.append(line.rstrip())


while node:
	if node.surface in josho: #上昇の表現か、下降の表現か
		p_hendo = 1

	elif node.surface in kako:
		p_hendo = -1

	node = node.next

f = open(file_name + '.csv', "rU") #データファイル読み込み(備考：日付の表記は全て2桁[8-2]→[8-02])
dataReader = csv.reader(f)

for a in dataReader: #配列dataにファイルデータ格納
	if a != ["date", "close"]: #一行目のdata,closeは描写用なので除く
		data_original.append(a)

for i in range(0, len(data_original)): #データを処理できる形に変更
	data_original[i][1] = float(data_original[i][1]) #数値をfloat型に変換

	#print data[i] #配列表示(テスト用)
	#データ例 ['8-01',100.0]

	#日付を整数表記にする
	date = data_original[i][0]
	date = date.replace('-','') #日付のハイフン削除
	date = int(date) #数値に変換 '801'=801
	data.append([date, data_original[i][1]])
	#データ例 [801,100.0]


hendo_rate = 0 #変動の一致度
max_min = 0 #変動一致度の1つ、始点終点が変動の曖昧表現にあった最大値最小値を満たしているか
wariai =0 #変動一致度の1つ、任意の二点間で変動の曖昧表現を満たす部分の割合
kikan_rate = 0 #期間の一致度
kikanS_rate = 0 #開始日の一致度
kikanE_rate = 0 #終了日の一致度
rate = 0 #変動と期間の一致度を考慮した、任意の2点間の最終的一致度
best_rate = 0 #現在最高の一致度を格納
second_rate = 0
third_rate = 0
fourth_rate = 0
fifth_rate = 0
best_start_data = 0 #現在最高の一致度の開始日
best_end_data = 0
second_start_data = 0
second_end_data = 0
third_start_data = 0
third_end_data = 0
fourth_start_data = 0
fourth_end_data = 0
fifth_start_data = 0
fifth_end_data = 0

next_kukan = []#隣り合う部分区間の上昇下降
sum_kukan = 0 #任意の2点間に変動表現を満たす部分区間がいくつあるか


for d in range(0, len(data)-1): #隣り合う2点間が上昇か下降かを見る(変動の一致度を測るための前処理)
	if p_hendo > 0: #上昇の場合
		if data[d][1] < data[d+1][1]:
			next_kukan.append(1)
		else:
			next_kukan.append(0)

	elif p_hendo <0: #下降の場合
		if data[d][1] > data[d+1][1]:
			next_kukan.append(1)
		else:
			next_kukan.append(0)

#print next_kukan #区間ごとの判断結果の確認用


for start_data in range(0, len(data)-1): #時系列データの中から任意の2点を1組ずつ見ていき、一致度を測る
	for end_data in range(start_data+1, len(data)): #任意の2点のうち、片方でも補完した時系列データなら一致度は測らない

		#上昇の場合
		if p_hendo > 0:
			#任意の2点が2点間で始点=最小値、終点=最大値を取っているか
			maxVal = -sys.maxint #任意の2点内での最大値格納
			maxDay = 0 #最大値を記録した日付(後でstart_dataと同じ日付か比較)
			minVal = sys.maxint #任意の2点内での最小値格納
			minDay = 0 #最小値を記録した日付(後でend_dataと同じ日付か比較)
			for i in range(start_data, end_data+1):
				if maxVal < data[i][1]:
					maxVal = data[i][1]
					maxDay = i

				if minVal > data[i][1]:
					minVal = data[i][1]
					minDay = i

			if maxDay == end_data and minDay == start_data:
				max_min = 1
			else:
				max_min = 0


			#変動一致度の1つ、任意の二点間で変動の曖昧表現を満たす部分の割合を測る
			sum_kukan = 0
			for d in range(start_data, end_data):
				sum_kukan = sum_kukan + next_kukan[d]

			try:
			    wariai = float(sum_kukan) / (end_data - start_data)
			except ZeroDivisionError:
				print("ZeroDivisionError!!")

			hendo_rate = float(max_min * wariai)


		#下降の場合
		elif p_hendo < 0:
			#任意の2点が2点間で始点=最小値、終点=最大値を取っているか
			maxVal = -sys.maxint #任意の2点内での最大値格納
			maxDay = 0 #最大値を記録した日付(後でstart_dataと同じ日付か比較)
			minVal = sys.maxint #任意の2点内での最小値格納
			minDay = 0 #最小値を記録した日付(後でend_dataと同じ日付か比較)
			for i in range(start_data, end_data+1):
				if maxVal < data[i][1]:
					maxVal = data[i][1]
					maxDay = i

				if minVal > data[i][1]:
					minVal = data[i][1]
					minDay = i

			if maxDay == start_data and minDay == end_data:
				max_min = 1
			else:
				max_min = 0

			#変動一致度の1つ、任意の二点間で変動の曖昧表現を満たす部分の割合を測る
			sum_kukan = 0
			for d in range(start_data, end_data):
				sum_kukan = sum_kukan + next_kukan[d]
				try:
				    wariai = float(sum_kukan) / (end_data - start_data)
				except ZeroDivisionError:
					print("ZeroDivisionError!!")

			hendo_rate = max_min * wariai

		#期間に関する一致度を測る
		s_y = data[start_data][0] / 10000 #(時系列データの任意の2点内の)開始日の年を求める
		e_y = data[end_data][0] / 10000 #終了日の年
		s_m = data[start_data][0] / 100 % 100 #開始日の月
		e_m = data[end_data][0] / 100 % 100 #終了日の月
		s_d = data[start_data][0] % 100 #開始日の日
		e_d = data[end_data][0] % 100 #終了日の日

		if p_kikan == "上旬":
			if p_year == s_y and p_year == e_y and p_month == s_m and p_month == e_m: #年月までが文書と同じ
				print "in"
				if s_d <= 11: #上旬開始日のファジィ
					kikanS_rate = float(11 - s_d) / 10
				else:
					kikanS_rate = 0

				if  e_d <= 11: #上旬終了日ファジィ
					kikanE_rate = float(e_d - 1) / 10
				elif e_d <= 21:
					kikanE_rate = float(21 - e_d) / 10
				else:
					kikanE_rate = 0

			else:
				kikanS_rate = 0
				kikanE_rate = 0

			print data[start_data][0],data[end_data][0]

		elif p_kikan == "中旬":
			if p_year == s_y and p_year == e_y and p_month == s_m and p_month == e_m: #年月までが文書と同じ
				if s_d < 5 : #中旬開始日のファジィ
					kikanS_rate = 0
				elif s_d <= 10:
					kikanS_rate = float(s_d - 5) / 5
				elif s_d <= 20:
					kikanS_rate = float(20 - s_d) / 10
				else:
					kikanS_rate = 0

				if  e_d < 10: #中旬終了日ファジィ
					kikanE_rate = 0
				elif e_d <= 20:
					kikanE_rate = float(e_d - 10) / 10
				elif e_d <= 25:
					kikanE_rate = float(25 - e_d) / 5
				else:
					kikanE_rate = 0

			else:
				kikanS_rate = 0
				kikanE_rate = 0

		elif p_kikan == "下旬":
			if p_year == s_y and p_year == e_y and p_month == s_m and p_month == e_m: #年月までが文書と同じ
				if s_d < 11 : #下旬開始日のファジィ
					kikanS_rate = 0
				elif s_d <= 21:
					kikanS_rate = float(s_d - 11) / 10
				elif s_d <= 31:
					kikanS_rate = float(31 - s_d) / 10
				else:
					kikanS_rate = 0

				if  e_d < 21: #下旬終了日ファジィ
					kikanE_rate = 0
				elif end_data <= 31:
					kikanE_rate = float(e_d - 21) / 10
				else:
					kikanE_rate = 0
			else:
				kikanS_rate = 0
				kikanE_rate = 0


		elif p_kikan == "初頭":
			if p_year == s_y and p_year == e_y and p_month == s_m and p_month == e_m: #年月までが文書と同じ
				if s_d <= 6: #初頭開始日のファジィ
					kikanS_rate = float(6 - s_d) / 5
				else:
					kikanS_rate = 0

				if  e_d < 5: #初頭終了日ファジィ
					kikanE_rate = 0
				elif end_data <= 10:
					kikanE_rate = float(e_d - 5) / 5
				elif end_data <= 15:
					kikanE_rate = float(15 - e_d) / 5
				else:
					kikanE_rate = 0

			else:
				kikanS_rate = 0
				kikanE_rate = 0

		elif p_kikan == "末":
			if p_year == s_y and p_year == e_y and p_month == s_m and p_month == e_m: #年月までが文書と同じ
				if s_d < 16: #末開始日のファジィ
					kikanS_rate = 0
				elif s_d <= 21:
					kikanS_rate = float(s_d - 16) / 5
				elif end_data <= 26:
					kikanS_rate = float(26 - s_d) / 5
				else:
					kikanS_rate = 0

				if  e_d < 26: #末終了日ファジィ
					kikanE_rate = 0
				elif end_data <= 31:
					kikanE_rate = float(e_d - 26) / 5
				else:
					kikanE_rate = 0

			else:
				kikanS_rate = 0
				kikanE_rate = 0


		else:
			pass

		kikan_rate = kikanS_rate * kikanE_rate

		rate = hendo_rate * kikan_rate
		if best_rate < rate:
			fifth_rate = fourth_rate
			fifth_start_data = fourth_start_data
			fifth_end_data = fourth_end_data
			fourth_rate = third_rate
			fourth_start_data = third_start_data
			fourth_end_data = third_end_data
			third_rate = second_rate
			third_start_data = second_start_data
			third_end_data = second_end_data
			second_rate = best_rate
			second_start_data = best_start_data
			second_end_data = best_end_data
			best_rate = rate
			best_start_data = start_data
			best_end_data = end_data


		elif second_rate < rate:
			fifth_rate = fourth_rate
			fifth_start_data = fourth_start_data
			fifth_end_data = fourth_end_data
			fourth_rate = third_rate
			fourth_start_data = third_start_data
			fourth_end_data = third_end_data
			third_rate = second_rate
			third_start_data = second_start_data
			third_end_data = second_end_data
			second_rate = rate
			second_start_data = start_data
			second_end_data = end_data

		elif third_rate < rate:
			fifth_rate = fourth_rate
			fifth_start_data = fourth_start_data
			fifth_end_data = fourth_end_data
			fourth_rate = third_rate
			fourth_start_data = third_start_data
			fourth_end_data = third_end_data
			third_rate = rate
			third_start_data = start_data
			third_end_data = end_data

		elif fourth_rate < rate:
			fifth_rate = fourth_rate
			fifth_start_data = fourth_start_data
			fifth_end_data = fourth_end_data
			fourth_rate = rate
			fourth_start_data = start_data
			fourth_end_data = end_data

		elif fifth_rate < rate:
			fifth_rate = rate
			fifth_start_data = start_data
			fifth_end_data = end_data


print "Content-Type:text/javascript"
print
print "callback({'answer':'%d'});"%(data[best_start_data][0])

#一致度が高い上位5件の期間を表示
# print "best:%d-%d(%f)"%(data[best_start_data][0],data[best_end_data][0],best_rate)
# print "second:%d-%d(%f)"%(data[second_start_data][0],data[second_end_data][0],second_rate)
# print "third:%d-%d(%f)"%(data[third_start_data][0],data[third_end_data][0],third_rate)
# print "fourth:%d-%d(%f)"%(data[fourth_start_data][0],data[fourth_end_data][0],fourth_rate)
# print "fifth:%d-%d(%f)"%(data[fifth_start_data][0],data[fifth_end_data][0],fifth_rate)

#一致度が最高の期間をcsvへの書き出し
f = open(file_name + '_result.csv','w') #ファイルが無ければ作る、の'a'を指定します
csvWriter = csv.writer(f)
write_flag = False

csvWriter.writerow(['date','close']) #一行目は決まっているので直接記入

for i in range(0, len(data_original)): #入力に用いたcsvデータをもとに,開始日〜終了日の部分だけを書き出す
	write_data = [] #書き出すデータを格納

	if i == best_start_data: #データが開始日になったら各行書き出す
		write_flag = True

	if write_flag == True:
		for j in range(0, 2):
			write_data.append(data_original[i][j])
		# print write_data;
		csvWriter.writerow(write_data)

	if i == best_end_data: #データが終了日になったら書き出し終了
		break

f.close

# print("書き出しが正常に完了しました")