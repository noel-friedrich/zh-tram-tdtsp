from tkinter import *

class NeuralDisplay:

    def show(self, nodes, size):
        root  = Tk()

        canvas = Canvas(root, width=size[0], height=size[1])
        canvas.pack()

        max_link = self.get_max(nodes)
        for i in range(1, len(nodes)):
            for k in range(len(nodes[i])):
                for j in range(len(nodes[i][k]["weights"])):
                    x1, y1 = self.get_node_coords(nodes, i, k, size)
                    x2, y2 = self.get_node_coords(nodes, i-1, j, size)
                    c, w = self.get_color(nodes[i][k]["weights"][j], max_link)
                    canvas.create_line(x1, y1, x2, y2, fill=c, width=w)

        for node, x_pos in zip(nodes, self.get_layer_pos(nodes, size[0])):
            for y_pos in self.get_layer_pos(node, size[1]):
                self.circle(canvas, x_pos, y_pos, 30)

        mainloop()

    def get_max(self, nodes):
        maximal = 0
        for i in range(1, len(nodes)):
            for k in range(len(nodes[i])):
                for j in range(len(nodes[i][k]["weights"])):
                    if abs(nodes[i][k]["weights"][j]) > maximal:
                        maximal = abs(nodes[i][k]["weights"][j])
        return maximal

    def get_color(self, value, max_link):
        if max_link == 0: max_link = 1
        percent = 100 * abs(value) / max_link
        if value > 0: out = "#0000" + format(int(percent)*2, '#04x')[2:]
        if value <= 0: out = "#" + format(int(percent)*2, '#04x')[2:] + "0000"
        return out, percent / 15

    def get_node_coords(self, nodes, i, node, size):
        x = (i + 1) * (size[0] // (len(nodes) + 1))
        y = (node + 1) * (size[1] // (len(nodes[i]) + 1))
        return [x,y]

    def circle(self, canvas,x,y, r):
        id = canvas.create_oval(x-r,y-r,x+r,y+r, width=3)
        return id

    def get_layer_pos(self, nodes, size):
        step = size // (len(nodes) + 1)
        output_layer_pos = []
        for i in range(len(nodes)):
            output_layer_pos.append(step * (i + 1))
        return output_layer_pos