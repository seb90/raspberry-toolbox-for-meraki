from flask import Flask, request, Response

app = Flask(__name__)  # create instance


@app.route('/', methods=['POST'])  # define endpoint
def respond():
    """ if a webhook is incoming, return status code 200 and print the json """
    if request.method == 'POST':  # if POST
        print(request.json)  # print webhook (json input)
        return Response(status=200)  # return status code 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=19000)
