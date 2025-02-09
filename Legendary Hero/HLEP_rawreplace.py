import os
import pandas as pd

#choose excel file
dictionary = 'HLEP_rawreplace.xlsx'

#choose text file
txtfile = 'HLEP_GPT.txt'
txtfile2 = 'HLEP_CN.txt'

#read excel file
df = pd.read_excel(dictionary)

#get each column words
wrongWords = df['Korean'].values.tolist()
rightWords = df['English'].values.tolist()

#read text file
with open(txtfile, 'r', encoding='utf8') as file :
  filedata = file.read()

#replace wrong words with right words
repeats = len(wrongWords)
for x in range(repeats):
   filedata = filedata.replace(wrongWords[x], rightWords[x] + ' ')

for x in range(repeats):
   filedata = filedata.replace('* ', '*')
   filedata = filedata.replace(' .', '.')
   filedata = filedata.replace(' ,', ',')
   filedata = filedata.replace(' !', '!')
   filedata = filedata.replace(' ?', '?')
   filedata = filedata.replace(' …', '…')
   filedata = filedata.replace('" ', '"')
   filedata = filedata.replace(' "', '"')
   filedata = filedata.replace(' .', '.')
   filedata = filedata.replace(' 。', '。')
   filedata = filedata.replace(' ,', ',')
   filedata = filedata.replace(' !', '!')
   filedata = filedata.replace(' ?', '?')
   filedata = filedata.replace('"…"', '"……"')
   
#rewrite the file
with open(txtfile, 'w', encoding='utf8') as file:
  file.write(filedata)
