#!/usr/bin/env python3

import sys
from random import random

import math

import locale
import os
from datetime import datetime

import yaml
from jinja2 import Environment, FileSystemLoader

import numpy as np
from numpy.polynomial import Polynomial as P
import warnings
warnings.simplefilter('ignore', np.exceptions.RankWarning)
import matplotlib.pyplot as plt

SMALL_SIZE = 8
MEDIUM_SIZE = 10
BIGGER_SIZE = 12

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(THIS_DIR), trim_blocks=True)

input_file = open('config.yaml')

config = yaml.safe_load(input_file)

# Name, Cost per Box, Box Minimum (sqft/box), Hex Color, Color Weight Array.
# tiles: [
# ['Pearl Gloss', 13, 9.75, '#E8DDD5', [ 610, 377, 233, 144, 89, 55, 34 ]],
# ['Salt Creek Gloss', 13, 9.75, '#ECE9DF', [ 610, 377, 233, 144, 89, 55, 34, 21 ]],
# ['Alberta Blue Gloss', 13, 9.75, '#B0B7B6',  [ 21, 34, 55, 89, 144, 233, 377 ]],
#]

locale.setlocale(locale.LC_ALL, config['locale'])
tile_size_h = config['tile_size_h']
tile_size_w = config['tile_size_w']
height = config['height']
width = config['width']

if height % tile_size_h != 0:
    height = math.ceil(config['height'] / tile_size_h ) * tile_size_h
    print("Given pattern height %s not divisible by given tile height %s.\nAdjusting pattern height to %s." % (config['height'], tile_size_h, height))
elif width % tile_size_w != 0:
    width = math.ceil(config['width'] / tile_size_w ) * tile_size_w
    print("Given pattern width %s not divisible by given tile width %s.\nAdjusting pattern width to %s." % (config['width'], tile_size_w, width))

width = math.ceil(config['width'] / tile_size_w ) * tile_size_w
rows = int(height / tile_size_h)
cols = int(width / tile_size_w)
num_colors = len(config['tiles'])



print("\nPattern Dimensions:\nHeight: %s, Width: %s \nRows: %s, Columns: %s \nNumber of Tile Colors: %s" % (height, width, rows, cols, num_colors))

if height % tile_size_h != 0:
    sys.exit("height not divisible by tile_size_h")
elif width % tile_size_w != 0:
    sys.exit("width not divisible by tile_size_w")

sq_footage_per_tile = float(( tile_size_w * tile_size_h ) / 144)

tile_sqft_per_boxes = []
colors = []
costs_per_sqft = []
formatted_costs = []
formatted_tile_prices = []
names = []
tile_prices = []
weights = []
for i, array in enumerate(config['tiles']):
        name = array[0]
        names.append(name)
        cost_per_sqft = array[1]
        costs_per_sqft.append(cost_per_sqft)
        formatted_costs.append(locale.currency(cost_per_sqft, symbol=True, grouping=True))
        tile_price = cost_per_sqft * sq_footage_per_tile
        tile_prices.append(tile_price)
        formatted_tile_prices.append(locale.currency(tile_price, symbol=True, grouping=True))
        tile_sqft_per_box = array[2]
        tile_sqft_per_boxes.append(tile_sqft_per_box)
        hex_color = array[3]
        colors.append(hex_color)
        color_weights = array[4]
        x = list(range(len(color_weights)))
        y = color_weights
        coeffs = np.polyfit(x,y,len(color_weights))
        # print("Color Weight polynomial for %s:\n%s" % (name, P(coeffs)))
        scale_factor = (len(color_weights)-1)/rows
        xx = np.multiply(list(range(rows)), scale_factor)
        x_rescaled = np.multiply(x, scale_factor)
        yy = np.polyval(coeffs, xx)
        weights.append(yy)
        label_name = name + ' ' + str(color_weights)
        plt.plot(yy, 'X-', color=hex_color, label=label_name)

plt.legend(loc='best')

tile_sqft_per_boxes_array = np.array(tile_sqft_per_boxes)
colors_array = np.array(colors)
costs_per_sqft_array = np.array(costs_per_sqft)
tile_prices_array = np.array(tile_prices)
formatted_costs_array = np.array(formatted_costs)
formatted_tile_prices_array = np.array(formatted_tile_prices)
names_array = np.array(names)
weights_array = np.array(weights)

grid = [[0 for x in range(cols)] for y in range(rows)]
zipped_colors = list(zip(*np.array(weights)))
area_totals = map(sum, zipped_colors)
buckets = [[0 for x in range(num_colors)] for y in range(rows)]
tile_counts = [0 for x in range(num_colors + 1)]

for s_idx, total in enumerate(area_totals):

    whole = 0.0

    for c_idx, color_weight in enumerate(zipped_colors[s_idx]):
        ratio = color_weight / float(total)
        value = whole + ratio
        whole += ratio

        buckets[s_idx][c_idx] = value

for s_idx, area in enumerate(buckets):
    for r_idx in range(1):

        row_n = s_idx + r_idx

        for c_idx in range(cols):
            r = random()

            for color_idx, p in enumerate(area):
                if r <= p:
                    grid[row_n][c_idx] = color_idx
                    tile_counts[color_idx] += 1
                    break

minimum_box_buy = list(map(lambda x,y:math.ceil(x * sq_footage_per_tile / y),tile_counts, tile_sqft_per_boxes))
tile_count_total = sum(tile_counts)

box_costs = list(map(lambda x,y,z:x*y*z,minimum_box_buy, tile_sqft_per_boxes, costs_per_sqft ))
formatted_box_costs = list(map(lambda x:locale.currency(x, symbol=True, grouping=True), box_costs))

total_cost = sum(box_costs)
formatted_total_cost = locale.currency(total_cost, symbol=True, grouping=True)

now = datetime.now()
job_id = 'tile_layout_' + str(height) + 'h_' + str(width) + 'w_' + 'tile_' + str(tile_size_h) + 'h_' + str(tile_size_w) + 'w—' + now.strftime("%d-%B-%Y-%H-%M-%S")
context = {
    'job_id': job_id,
    'config': config['tiles'],
    'tile_sqft_per_boxes': tile_sqft_per_boxes_array,
    'formatted_box_costs': formatted_box_costs,
    'colors': colors_array,
    'costs': formatted_costs_array,
    'tile_prices': formatted_tile_prices_array,
    'names': names_array,
    'grid': grid,
    'grid_w': width,
    'grid_h': height,
    'rows': rows,
    'minimum_box_buy': minimum_box_buy,
    'tile_size_w': tile_size_w,
    'tile_size_h': tile_size_h,
    'tile_counts': tile_counts,
    'tile_count_total': tile_count_total,
    'formatted_total_cost': formatted_total_cost,
    'charset': config['locale'].split('.')[1],
    'lang': config['locale'].split('_')[0],

}
print("Total Cost: %s" % (formatted_total_cost))


rendered_template = env.get_template('output.html.jinja').render(context)
output_dir = THIS_DIR + '/output'
os.makedirs(output_dir, exist_ok=True)
plt.savefig(output_dir + '/' + job_id + '_color_weight.png')
output_file_name = output_dir + '/' + job_id + '.html'
with open(output_file_name, 'w') as f:
    f.write(rendered_template)

print("Output is in: %s" % output_file_name)
