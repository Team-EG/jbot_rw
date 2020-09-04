import time
import flask
import flask_restful
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

app = flask.Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['UPLOAD_FOLDER'] = "images/"
api = flask_restful.Api(app)


def check_if_req_key_exist(req_keys, json_data):
    forgot = [x for x in req_keys if x not in json_data.keys()]
    why_none = [x for x in json_data.keys() if x in req_keys and json_data[x] is None and x != "params"]
    if len(forgot) != 0:
        return flask_restful.abort(400, description=f"Wrong json format. You forgot: {', '.join(forgot)}")
    if len(why_none) != 0:
        return flask_restful.abort(400, description=f"Values of required keys are None(null). Keys with None(null) value: {', '.join(why_none)}")
    return None


@app.route("/images/<path:file_name>")
def send_image(file_name):
    return flask.send_file("images/"+file_name)


class RequestImage(flask_restful.Resource):
    def post(self):
        current_time = round(time.time())
        req_keys = ["stock_list"]
        json_data = flask.request.get_json(force=True)
        res = check_if_req_key_exist(req_keys, json_data)
        if res is not None:
            return res
        mpl.rc('font', family="NanumBarunGothic")
        for x in json_data["stock_list"]:
            history = [int(a) for a in x["history"].split(',')]
            nums = [x for x in range(-len(history), 0)]
            plt.plot(nums, history, label=x["name"])
        plt.ylabel("가격 (원)")
        plt.legend(loc=1)
        plt.savefig(f'images/{current_time}.png', dpi=300)
        plt.cla()
        return f"http://jebserver.iptime.org:8901/images/{current_time}.png"


api.add_resource(RequestImage, "/request_image")
app.run(host="0.0.0.0", port="8901")
