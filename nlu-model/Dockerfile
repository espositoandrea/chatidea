FROM rasa/rasa

COPY credentials.yml .
COPY models/nlu_model.tar.gz .
EXPOSE 5005
CMD ["run", "--enable-api", "--credentials", "credentials.yml", "-m", "nlu_model.tar.gz"]
