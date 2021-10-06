import zmq, json, time


def send():
    context = zmq.Context()
    publisher = context.socket(zmq.REQ)
    publisher.connect("tcp://127.0.0.1:6555")
    data = {"method":"download","link":"https://www.youtube.com/watch?v=HNZRaeTpmJw"}
    publisher.send_json(data)
    message = publisher.recv()
    print(f"Request: 1 - [{message}]")



send()
