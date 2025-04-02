FROM rasa/rasa:3.6.0-full
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 5005
CMD ["run", "--enable-api", "--cors", "*"]
