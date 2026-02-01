FROM python:3.13-slim

WORKDIR /iptv

COPY config config
COPY output output
COPY merge.py merge.py
COPY m3u-sources.txt config/m3u-sources.txt

RUN pip install --no-cache-dir flask requests

EXPOSE 50087

CMD ["python", "merge.py"]
