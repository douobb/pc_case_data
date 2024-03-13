import requests
from bs4 import BeautifulSoup
import re
from firebase import firebase
import pandas as pd
from datetime import datetime,timezone,timedelta
import os

res = requests.get('https://www.coolpc.com.tw/eachview.php?IGrp=14')
soup = BeautifulSoup(res.text, "html.parser")
allCase = soup.find_all("span")

#標題
titles = soup.findAll(class_='t')
allBrands = ["Fractal Design","COUGAR","曜越","Apexgaming","SAMA","銀欣","台鼎環球","樹昌","B-Team","聯力","酷碼","Phanteks","全漢","darkFlash","abee","華碩","Montech","視博通","微星","技嘉","亞碩","旋剛","1st Player","Antec","BitFenix","HYTE","be quiet!","NZXT","賽德斯","喬思伯","迎廣","SSUPD","XPG","保銳","海盜船","海韻","i-CoolTw"]

#品牌
brands = []
for i in range(len(titles)):
  b=0
  titles[i] = str(titles[i].next_element)
  for j in range(len(allBrands)):
    if allBrands[j] in titles[i]:
      brands.append(allBrands[j])
      b=1
      break
  if (b==0):
    brands.append(0)

#尺寸
size = []
for case in allCase:
  if (len(case.find_all(string=re.compile("尺寸")))==1):
    size.append(case.find_all(string=re.compile("尺寸"))[0].replace("尺寸：",""))
  else:
    size.append(('/'.join(case.find_all(string=re.compile("尺寸")))).replace("尺寸：",""))

#容量
volume = []
for i in range(len(size)):
  if (("~" in size[i]) or ("(" in size[i])):
    if(size[i].count("*")==2):
      tmp = (size[i]).split("*")
      volume.append(round(min([float(x) for x in re.findall(r'-?\d+\.?\d*',tmp[0])])*min([float(x) for x in re.findall(r'-?\d+\.?\d*',tmp[1])])*min([float(x) for x in re.findall(r'-?\d+\.?\d*',tmp[2])])/1000,1))
    else:
      tmp = (size[i]).split("/")
      t1 = [float(x) for x in re.findall(r'-?\d+\.?\d*',tmp[0])]
      t2 = [float(x) for x in re.findall(r'-?\d+\.?\d*',tmp[1])]
      volume.append(round(min(t1[0]*t1[1]*t1[2]/1000,t2[0]*t2[1]*t2[2]/1000),1))
  else:
    tmp = (size[i]).split("*")
    volume.append(round(float(tmp[0])*float(tmp[1])*float(tmp[2])/1000,1))

#顯卡長度
GPULength = []
#CPU高度
CPUHeight = []
for title in titles:
  if (("卡" in title) and (float(re.findall(r'-?\d+\.?\d*',title[title.find("卡"):])[0])>10)):
    GPULength.append(float(re.findall(r'-?\d+\.?\d*',title[title.find("卡"):])[0]))
  else:
    GPULength.append(0)
  if "U高" in title:
    CPUHeight.append(float(re.findall(r'-?\d+\.?\d*',title[title.find("U高"):])[0]))
  elif "/U" in title:
    CPUHeight.append(float(re.findall(r'-?\d+\.?\d*',title[title.find("/U"):])[0]))
  elif "/CPU" in title:
    CPUHeight.append(float(re.findall(r'-?\d+\.?\d*',title[title.find("/CPU"):])[0]))
  else:
    CPUHeight.append(0)

#支援水冷
liquidCooling = []
for case in allCase:
  if (len(case.find_all(string=re.compile("支援水冷")))!=0):
    if "支援水冷散熱排：" in case.find_all(string=re.compile("支援水冷"))[0]:
      liquidCooling.append(case.find_all(string=re.compile("支援水冷"))[0].replace("支援水冷散熱排：",""))
    if "支援水冷：" in case.find_all(string=re.compile("支援水冷"))[0]:
      liquidCooling.append(case.find_all(string=re.compile("支援水冷"))[0].replace("支援水冷：",""))
  else:
    liquidCooling.append("無")

#支援水冷細項
liquidCoolingDetail = [["120",[]],["140",[]],["240",[]],["280",[]],["360",[]],["420",[]]]
for LC in liquidCooling:
  for i in range(6):
    if liquidCoolingDetail[i][0] in LC:
      liquidCoolingDetail[i][1].append(1)
    else:
      liquidCoolingDetail[i][1].append(0)

#硬碟空間
drivesSupport = []
for case in allCase:
  if (len(case.find_all(string=re.compile("硬碟空間")))==1):
    drivesSupport.append((case.find_all(string=re.compile("硬碟空間"))[0].replace("硬碟空間：","")).replace(" *註1*",""))
  else:
    drivesSupport.append(('|'.join(case.find_all(string=re.compile("硬碟空間")))).replace("硬碟空間：",""))

#硬碟空間細項
drivesSupportDetail = [["2.5",[]],["3.5",[]]]
for drives in drivesSupport:
  for i in range(2):
    if drivesSupportDetail[i][0] in drives:
      drivesSupportDetail[i][1].append(1)
    else:
      drivesSupportDetail[i][1].append(0)

#光碟機
CDSupport = []
for drives in drivesSupport:
  if "5.25" in drives:
    CDSupport.append(int(drives[(drives.find("*"))+1]))
  else:
    CDSupport.append(0)

#內附風扇
fansInside = []
#內附風扇總數
fansInsideCount = []
for case in allCase:
  if (len(case.find_all(string=re.compile("內附風扇")))!=0):
    fansInside.append(case.find_all(string=re.compile("內附風扇"))[0].replace("內附風扇：",""))
  else:
    fansInside.append("無")
for fans in fansInside:
  if (fans=="無"):
    fansInsideCount.append(0)
  else:
    c=0
    for i in range(len(fans)):
      if (fans[i]=="*"):
        c += int(fans[i+1])
    fansInsideCount.append(c)

#風扇支援
fansSupport = []
for case in allCase:
  if (len(case.find_all(string=re.compile("風扇支援")))!=0):
    if (len(case.find_all(string=re.compile("風扇支援")))!=1):
      fansSupport.append((('|'.join(case.find_all(string=re.compile("風扇支援")))).replace("風扇支援：","")).replace(" *註1*",""))
    else:
      fansSupport.append((case.find_all(string=re.compile("風扇支援"))[0].replace("風扇支援：","")).replace(" *註1*",""))
  else:
    fansSupport.append("無")

#風扇支援細項 (前,後,上,下,側)
fansSupportDetail = [[],[],[],[],[]]
for i in range(len(fansSupport)):
  if ("前" in (fansSupport[i]+fansInside[i])):
    fansSupportDetail[0].append(1)
  else:
    fansSupportDetail[0].append(0)
  if ("後" in (fansSupport[i]+fansInside[i])):
    fansSupportDetail[1].append(1)
  else:
    fansSupportDetail[1].append(0)
  if ("上" in (fansSupport[i]+fansInside[i])):
    fansSupportDetail[2].append(1)
  else:
    fansSupportDetail[2].append(0)
  if (("下" in (fansSupport[i]+fansInside[i])) or ("底" in (fansSupport[i]+fansInside[i])) or ("電源艙" in (fansSupport[i]+fansInside[i])) or ("電源倉" in (fansSupport[i]+fansInside[i]))):
    fansSupportDetail[3].append(1)
  else:
    fansSupportDetail[3].append(0)
  if (("側" in (fansSupport[i]+fansInside[i])) or ("左" in (fansSupport[i]+fansInside[i])) or ("右" in (fansSupport[i]+fansInside[i]))):
    fansSupportDetail[4].append(1)
  else:
    fansSupportDetail[4].append(0)

#I/O
frontIO = []
for case in allCase:
  if (len(case.find_all(string=re.compile("前I/O")))!=0):
    frontIO.append(case.find_all(string=re.compile("前I/O"))[0].replace("前I/O：",""))
  else:
    if (len(case.find_all(string=re.compile("側I/O")))!=0):
      frontIO.append(case.find_all(string=re.compile("側I/O"))[0].replace("側I/O：",""))
    else:
      frontIO.append("")

import re
#I/O細項
I_O = [["U3",[]],["U2",[]],["TYPE-C",[]],["HDMI",[]],["SD讀卡機",[]]]
for ports in frontIO:
  for i in range(4):
    if I_O[i][0] in ports:
      I_O[i][1].append(int((ports[ports.find(I_O[i][0]):])[((ports[ports.find(I_O[i][0]):]).find("*"))+1]))
    else:
      I_O[i][1].append(0)
for case in allCase:
  if(len(case.find_all(string=re.compile("SD讀卡")))!=0):
    I_O[4][1].append(1)
  else:
    I_O[4][1].append(0)

#主板相容(0:EATX 1:ATX 2:MATX 3:ITX)
motherboardCompatibility = []
for title in titles:
  if (("E-ATX" in title) or ("EEB" in title)):
    motherboardCompatibility.append(0)
  elif "M-ATX" in title:
    motherboardCompatibility.append(2)
  elif "ITX" in title:
    motherboardCompatibility.append(3)
  elif "ATX" in title:
    motherboardCompatibility.append(1)
  else:
    motherboardCompatibility.append(4)

#價格
price = []
for case in allCase:
  price.append(int(((case.find_all(string=re.compile("含稅：NT"))[0].replace("含稅：NT","").split())[0])))

import re
#電供規格限制
sfxPSU = []
for title in titles:
  if ("SFX" in title):
    sfxPSU.append(1)
  else:
    sfxPSU.append(0)

import re
#側板類型(0:透側 1:非透側 2:可替換透測或非透測)
sidePanel = []
for case in allCase:
  if (len(case.find_all(string=re.compile("TG|側透|透側|透測|透明|玻璃|全透")))!=0):
    if (len(case.find_all(string=re.compile("酷碼 MasterBox NR200P")))!=0):
      sidePanel.append(2)
    else:
      sidePanel.append(0)
  else:
    sidePanel.append(1)

#控制器&集線器
fanHub = []
for case in allCase:
  if (len(case.find_all(string=re.compile("控制器|集線器")))!=0):
    fanHub.append(1)
  else:
    fanHub.append(0)

#顯卡垂直安裝
verticalGPU = []
for case in allCase:
  if (len(case.find_all(string=re.compile("顯卡垂直安裝")))!=0):
    verticalGPU.append(1)
  else:
    verticalGPU.append(0)

#贈禮
gift = []
for case in allCase:
  if (len(case.findAll(class_='g'))!=0):
    gift.append(str(case.findAll(class_='g')[0].next_element))
  else:
    gift.append("無")

#細節文字
detail = []
for case in allCase:
  c = []
  for string in case.stripped_strings:
    c.append(str(string).replace(" \xa0♦",""))
  while ("含稅：" not in c[-1]):
    del c[-1]
  del c[-1]
  del c[0]
  detail.append("\n".join(c))

#圖片
images = []
for image in soup.find_all("img"):
  images.append("https://www.coolpc.com.tw"+str(image.get("src")))

#開箱連結
links = []
for case in allCase:
  if (len(case.findAll("a"))!=0):
    for link in case.find_all("a"):
      if (str(link.get("href"))[0]=="/"):
        links.append("https://www.coolpc.com.tw"+str(link.get("href")))
      else:
        links.append(str(link.get("href")))
  else:
    links.append("無")

#例外處理
for i in range(len(titles)):
  #容量
  if("RM23-502" in titles[i]):
    volume[i]/=10
  #I/O
  if("聯力 ODYSSEY X" in titles[i]):
    frontIO[i] = "U3*2+TYPE-C*1"
    I_O[0][1][i] = 2
    I_O[1][1][i] = 0
    I_O[2][1][i] = 1
    I_O[3][1][i] = 0
    I_O[4][1][i] = 0
  #主板相容
  if("Ceres 300 TG" in titles[i]):
    motherboardCompatibility[i] = 1
  #電供規格限制
  if("銀欣 SUGO 16" in titles[i] or "abee AS Enclosure RS07" in titles[i]):
    sfxPSU[i] = 0
  #側板類型
  if("華碩 TUF Gaming GT502" in titles[i] or "微星 MAG PANO M100R PZ" in titles[i] or "微星 MPG GUNGNIR 110R WHITE" in titles[i] or "微星 MPG VELOX 100R WHITE" in titles[i]):
    sidePanel[i] = 0

#創建CSV
df = {"機殼":[],"品牌":[],"容量":[],"顯卡長":[],"CPU高":[],"主板":[],"電供":[],"內附風扇數":[],"風扇前":[],"風扇後":[],"風扇上":[],"風扇下":[],"風扇側":[],"水冷120":[],"水冷140":[],"水冷240":[],"水冷280":[],"水冷360":[],"水冷420":[],"IO_U3":[],"IO_U2":[],"IO_TYPE-C":[],"IO_HDMI":[],"IO_SD讀卡機":[],"硬碟2.5":[],"硬碟3.5":[],"光碟機":[],"側板類型":[],"控制器&集線器":[],"顯卡垂直安裝":[],"圖片":[],"開箱連結":[],"贈禮":[],"價格":[]}
for i in range(len(titles)):
  df["機殼"].append(titles[i])
  df["品牌"].append(brands[i])
  df["容量"].append(volume[i])
  df["顯卡長"].append(GPULength[i])
  df["CPU高"].append(CPUHeight[i])
  df["主板"].append(motherboardCompatibility[i])
  df["電供"].append(sfxPSU[i])
  df["內附風扇數"].append(fansInsideCount[i])
  df["風扇前"].append(fansSupportDetail[0][i])
  df["風扇後"].append(fansSupportDetail[1][i])
  df["風扇上"].append(fansSupportDetail[2][i])
  df["風扇下"].append(fansSupportDetail[3][i])
  df["風扇側"].append(fansSupportDetail[4][i])
  df["水冷120"].append(liquidCoolingDetail[0][1][i])
  df["水冷140"].append(liquidCoolingDetail[1][1][i])
  df["水冷240"].append(liquidCoolingDetail[2][1][i])
  df["水冷280"].append(liquidCoolingDetail[3][1][i])
  df["水冷360"].append(liquidCoolingDetail[4][1][i])
  df["水冷420"].append(liquidCoolingDetail[5][1][i])
  df["IO_U3"].append(I_O[0][1][i])
  df["IO_U2"].append(I_O[1][1][i])
  df["IO_TYPE-C"].append(I_O[2][1][i])
  df["IO_HDMI"].append(I_O[3][1][i])
  df["IO_SD讀卡機"].append(I_O[4][1][i])
  df["硬碟2.5"].append(drivesSupportDetail[0][1][i])
  df["硬碟3.5"].append(drivesSupportDetail[1][1][i])
  df["光碟機"].append(CDSupport[i])
  df["側板類型"].append(sidePanel[i])
  df["控制器&集線器"].append(fanHub[i])
  df["顯卡垂直安裝"].append(verticalGPU[i])
  df["圖片"].append(images[i])
  df["開箱連結"].append(links[i])
  df["贈禮"].append(gift[i])
  df["價格"].append(price[i])

df = pd.DataFrame.from_dict(df)
df.to_csv("pc_case.csv",index = False,encoding = "utf-8-sig")

#上傳firebase
url = os.environ['SECRET_LINK'] #SECRET_LINK為firebase儲存庫連結
fdb = firebase.FirebaseApplication(url, None) 
fdb.delete('/', None)
for i in range(len(titles)):
  fdb.put('/',"case "+str(i+1).zfill(3),{
    "titles" : titles[i],
    "brands" : brands[i],
    "volume" : volume[i],
    "GPULength" : GPULength[i],
    "CPUHeight" : CPUHeight[i],
    "motherboardCompatibility" : motherboardCompatibility[i],
    "sfxPSU" : sfxPSU[i],
    "fansInsideCount" : fansInsideCount[i],
    "fanSupportFront" : fansSupportDetail[0][i],
    "fanSupportBack" : fansSupportDetail[1][i],
    "fanSupportTop" : fansSupportDetail[2][i],
    "fanSupportBottom" : fansSupportDetail[3][i],
    "fanSupportSide" : fansSupportDetail[4][i],
    "LC120" : liquidCoolingDetail[0][1][i],
    "LC140" : liquidCoolingDetail[1][1][i],
    "LC240" : liquidCoolingDetail[2][1][i],
    "LC280" : liquidCoolingDetail[3][1][i],
    "LC360" : liquidCoolingDetail[4][1][i],
    "LC420" : liquidCoolingDetail[5][1][i],
    "IO_U3" : I_O[0][1][i],
    "IO_U2" : I_O[1][1][i],
    "IO_TYPE_C" : I_O[2][1][i],
    "IO_HDMI" : I_O[3][1][i],
    "IO_SDReader" : I_O[4][1][i],
    "drivesSupport25" : drivesSupportDetail[0][1][i],
    "drivesSupport35" : drivesSupportDetail[1][1][i],
    "CDSupport" : CDSupport[i],
    "sidePanel" : sidePanel[i],
    "fanHub" : fanHub[i],
    "verticalGPU" : verticalGPU[i],
    "images" : images[i],
    "links" : links[i],
    "gift" : gift[i],
    "price" : price[i],
    "detail" : detail[i],
  })
with open('log.txt', 'a') as f:
    f.write(str(datetime.now().astimezone(timezone(timedelta(hours=8))).strftime("%Y/%m/%d %H:%M:%S"))+" update "+str(len(titles))+" data\n")