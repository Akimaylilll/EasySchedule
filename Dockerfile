FROM python:3.7.3
MAINTAINER Maylilll <642722474@qq.com>
COPY . /app
WORKDIR /app
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN echo 'Asia/Shanghai' >/etc/timezone
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple multiprocessing_on_dill
# EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["src/main.py"]