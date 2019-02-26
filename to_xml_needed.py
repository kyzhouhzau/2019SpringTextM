#! usr/bin/env python3
# -*- coding:utf-8 -*-
'''
Author:zhoukaiyin
Time:2018年1月16日

'''
#该脚本用于将下载并重新命名后的xml文件整理成CRF所需要的格式。
from bs4 import BeautifulSoup as bs
import codecs
import os
import sys
import glob
inppath = sys.argv[1]
outpath = sys.argv[2]
if not os.path.exists(outpath):
    os.system("mkdir "+outpath)
files = glob.glob(inppath+"/*")
for file in files:
    filename = os.path.basename(file)
    print(filename)
    try:
        with codecs.open(file,'r',encoding='utf8') as rf:
            do=rf.read()
        with codecs.open(outpath+'/'+filename.split('.')[0]+'.xml','w',encoding='utf8') as wf:
            soup = bs(do,'lxml')
            txt=soup.document.text.replace('\n',' ')
            txt=txt.replace('<','&lt;')
            txt=txt.replace('>','&gt;')
            txt=txt.replace('&','')
            wf.write('<?xml version="1.0" encoding="UTF-8"?>'+'\n')
            wf.write('<Label drug="'+filename.split('.')[0]+'" track="TAC2017_ADR">'+'\n')
            wf.write('  <Text>'+'\n')
            wf.write('    <Section name="adverse reactions" id="S1">')
            wf.write(' '+txt)
            wf.write('\n'+'    </Section>'+'\n')
            wf.write('  </Text>'+'\n')
            wf.write('</Label>' + '\n')
            # wf.write(txt)
    except PermissionError:
        pass
