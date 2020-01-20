__author__ = 'Tomer Gross'
__date__ = 'January, 2020'

import socket


def main():
    host = '127.0.0.1'  # local host IP '127.0.0.1'
    port = 1005  # define the port on which you want to connect
    flag = 0  # used for detecting an empty message
    game_end = 0  # used to detect when game is over
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))  # connect to server on local computer
    data_history = []  # history of received messages
    while True:
        if flag == 0:  # in a case that the player send something to the server
            data = s.recv(1024).decode()  # message received from server
            data_history.append(data)
            print(data)  # print the received message
        else:
            data = data_history[-1]  # in a case that the player send an empty message

        if "Game" in data:  # received a game over message
            game_end = 1

        if "ended" in str(data) or "Max" in str(data):
            # if server disconnected the player because one of two reasons
            # game is over or there are already 2 players playing game
            break

        ans = input("Send: ")
        if ans == "":
            print("Don't send an empty string!")
            flag = 1
            continue
        else:
            flag = 0

        s.send(ans.encode())

        if ans == "no" and game_end == 1:  # exit the program in a case which the player decided not go for another game
            break
        elif ans == "yes" and game_end == 1:  # new game status if player decided go for another game
            game_end = 0

    s.close()  # close the connection


if __name__ == '__main__':
    main()
