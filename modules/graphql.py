class GraphQL:
    @staticmethod
    def build_query(query: str, *, params: dict = None, to_request: list = None):
        base = """query {
  __query__(__params__) {
    __to_request__
  }
}""".replace("__query__", query)
        if params is None:
            base = base.replace("(__params__)", "")
        else:
            _params = ', '.join([f"""{k}: {f'"{v}"' if type(v) == str else v}""" for k, v in params.items()])
            base = base.replace("__params__", _params)
        if to_request is None:
            base = base.replace(" {\n    __to_request__\n  }", "")
        else:
            base = base.replace("__to_request__", '\n    '.join(to_request))
        return base

    @staticmethod
    def build_mutation(mutation: str, *, params: dict = None, to_request: list = None):
        base = """mutation {
  __mutation__(__params__) {
    __to_request__
  }
}""".replace("__mutation__", mutation)
        if params is None:
            base = base.replace("(__params__)", "")
        else:
            _params = ', '.join([f"""{k}: {f'"{v}"' if type(v) == str else v}""" for k, v in params.items()])
            base = base.replace("__params__", _params)
        if to_request is None:
            base = base.replace(" {\n    __to_request__\n  }", "")
        else:
            base = base.replace("__to_request__", '\n    '.join(to_request))
        return base


if __name__ == "__main__":
    print(GraphQL.build_query("bot", params={"id": "6227103548367175801"}, to_request=["name", "servers"]))
