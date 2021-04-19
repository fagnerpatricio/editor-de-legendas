for arq in {13..24};
do
    indice=$arq
    if [ $arq -lt 10 ]
    then
        indice="0"$arq
    fi
    echo $indice
    mkvmerge --ui-language pt_BR --output "/mnt/KingstonSSD/Tratamento/Saida/Lucky Star (2007) S01E$indice.mkv" --audio-tracks 1 --no-subtitles --language 0:ja --default-track 0:yes --display-dimensions 0:1920x1080 --language 1:ja --default-track 1:yes '(' "/mnt/KingstonSSD/Tratamento/EP/Lucky Star (2007) S01E$indice.mkv" ')' --language 0:pt '(' "/mnt/KingstonSSD/Tratamento/LEG/Lucky Star (2007) S01E$indice.pt-br.ass" ')' --attachment-name nagurigaki-p.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/nagurigaki-p.ttf --attachment-name trebuchet-ms.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/trebuchet-ms.ttf --attachment-name tempus-sans-itc.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/tempus-sans-itc.ttf --attachment-name smudger-let.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/smudger-let.ttf --attachment-name one-stroke-script-let-plain.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/one-stroke-script-let-plain.ttf --attachment-name eras-medium-itc.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/eras-medium-itc.ttf --attachment-name comic-sans-ms-4.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/comic-sans-ms-4.ttf --attachment-name bell-gothic-std-black.otf --attachment-mime-type application/vnd.ms-opentype --attach-file /home/fagner/Downloads/Fontes/bell-gothic-std-black.otf --attachment-name arial.ttf --attachment-mime-type font/sfnt --attach-file /home/fagner/Downloads/Fontes/arial.ttf --track-order 0:0,0:1,1:0
done


    