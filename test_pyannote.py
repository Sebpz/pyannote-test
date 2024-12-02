from pyannote.audio import Pipeline
from pydub import AudioSegment
import time



# Step 2b: Speaker Diarization using Pyannote
def pyannote_diarization(audio_file_path):

    # Start the timer
    start_time = time.time()
    pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization@2.1',
                                        use_auth_token='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')
    dz = pipeline(audio_file_path, num_speakers=2)  

    with open("diarization.txt", "w") as text_file:
        text_file.write(str(dz))

    # End the timer
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")

    print(*list(dz.itertracks(yield_label = True))[:10], sep="\n")

audio_path = "Lucy_Phone_Call_[_YouConvert.net_].wav"
pyannote_diarization(audio_path)


audio = AudioSegment.from_wav("Lucy_Phone_Call_[_YouConvert.net_].wav")
spacermilli = 2000
spacer = AudioSegment.silent(duration=spacermilli)
audio = spacer.append(audio, crossfade=0)

audio.export('audio.wav', format='wav')
     
def millisec(timeStr):
  spl = timeStr.split(":")
  s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2]) )* 1000)
  return s

import re
dz = open('diarization.txt').read().splitlines()
dzList = []
for l in dz:
  start, end =  tuple(re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=l))
  start = millisec(start) - spacermilli
  end = millisec(end)  - spacermilli
  lex = not re.findall('SPEAKER_01', string=l)
  dzList.append([start, end, lex])

print(*dzList[:10], sep='\n')


import re 

sounds = spacer
segments = []

dz = open('diarization.txt').read().splitlines()
for l in dz:
  start, end =  tuple(re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=l))
  start = int(millisec(start)) #milliseconds
  end = int(millisec(end))  #milliseconds
  
  segments.append(len(sounds))
  sounds = sounds.append(audio[start:end], crossfade=0)
  sounds = sounds.append(spacer, crossfade=0)

sounds.export("dz.wav", format="wav") #Exports to a wav file in the current path.

import webvtt

captions = [[(int)(millisec(caption.start)), (int)(millisec(caption.end)),  caption.text] for caption in webvtt.read('dz.wav.vtt')]
print(*captions[:8], sep='\n')

# we need this fore our HTML file (basicly just some styling)
preS = '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <meta http-equiv="X-UA-Compatible" content="ie=edge">\n    <title>Lexicap</title>\n    <style>\n        body {\n            font-family: sans-serif;\n            font-size: 18px;\n            color: #111;\n            padding: 0 0 1em 0;\n        }\n        .l {\n          color: #050;\n        }\n        .s {\n            display: inline-block;\n        }\n        .e {\n            display: inline-block;\n        }\n        .t {\n            display: inline-block;\n        }\n        #player {\n\t\tposition: sticky;\n\t\ttop: 20px;\n\t\tfloat: right;\n\t}\n    </style>\n  </head>\n  <body>\n    <h2>Yann LeCun: Dark Matter of Intelligence and Self-Supervised Learning | Lex Fridman Podcast #258</h2>\n  <div  id="player"></div>\n    <script>\n      var tag = document.createElement(\'script\');\n      tag.src = "https://www.youtube.com/iframe_api";\n      var firstScriptTag = document.getElementsByTagName(\'script\')[0];\n      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);\n      var player;\n      function onYouTubeIframeAPIReady() {\n        player = new YT.Player(\'player\', {\n          height: \'210\',\n          width: \'340\',\n          videoId: \'SGzMElJ11Cc\',\n        });\n      }\n      function setCurrentTime(timepoint) {\n        player.seekTo(timepoint);\n   player.playVideo();\n   }\n    </script><br>\n'
postS = '\t</body>\n</html>'

from datetime import timedelta

html = list(preS)

for i in range(len(segments)):
  idx = 0
  for idx in range(len(captions)):
    if captions[idx][0] >= (segments[i] - spacermilli):
      break
  
  while (idx < (len(captions))) and ((i == len(segments) - 1) or (captions[idx][1] < segments[i+1])):
    c = captions[idx]  
    
    start = dzList[i][0] + (c[0] -segments[i])

    if start < 0: 
      start = 0
    idx += 1

    start = start / 1000.0
    startStr = '{0:02d}:{1:02d}:{2:02.2f}'.format((int)(start // 3600), 
                                            (int)(start % 3600 // 60), 
                                            start % 60)
    
    html.append('\t\t\t<div class="c">\n')
    html.append(f'\t\t\t\t<a class="l" href="#{startStr}" id="{startStr}">link</a> |\n')
    html.append(f'\t\t\t\t<div class="s"><a href="javascript:void(0);" onclick=setCurrentTime({int(start)})>{startStr}</a></div>\n')
    html.append(f'\t\t\t\t<div class="t">{"[Lex]" if dzList[i][2] else "[Yann]"} {c[2]}</div>\n')
    html.append('\t\t\t</div>\n\n')

html.append(postS)
s = "".join(html)

with open("lucy.html", "w") as text_file:
    text_file.write(s)
print(s)
