import os
import random
import sys

import numpy as np
from scipy.misc import imread

from .model import get_model

# Training script for the stop sign sliding window model, that divides up wide image slices produced from the same
# selection script as the other sliding window systems
# Created by brendon-ai, January 2018


# Check that the number of command line arguments is correct
if len(sys.argv) != 3:
    print('Usage:', sys.argv[0], '<trained model path> <image folder>')
    sys.exit()

# Get the provided arguments
model_path = sys.argv[1]
image_folder = sys.argv[2]

# Create lists to hold the images and examples
image_list = []
label_list = []

# For each of the files in the image directory
image_names = os.listdir(image_folder)
for image_name in image_names:
    # Get the image's horizontal stop sign position
    # Names should be in the format 'x[horizontal position]_y[vertical position]_[UUID].jpg'
    stop_sign_position = int(image_name.split('_')[0][1:])
    # Load the image from disk with its full path
    image_path = os.path.expanduser(image_folder + '/' + image_name)
    image = imread(image_path)
    # Get the window size, which is the height of the image
    window_size = image.shape[0]


    # Compute a slice start and a slice end given a horizontal center point
    def compute_slice(center_position):
        # Determine the horizontal starting and ending points of the window based on the global window size
        horizontal_slice_start = center_position - (window_size // 2)
        horizontal_slice_end = horizontal_slice_start + window_size

        # If the start is less than zero, or the end is greater than the width of the image, return None
        if horizontal_slice_start < 0 or horizontal_slice_end > image.shape[1]:
            return None
        # Otherwise return the start and end positions
        else:
            return horizontal_slice_start, horizontal_slice_end


    # Slice a block out of an image given a horizontal position and a width
    def slice_image(starting_point, ending_point):
        # Slice the image and return it
        return image[:, starting_point:ending_point]


    # Get the slice bounds for the positive example
    true_slice_bounds = compute_slice(stop_sign_position)
    # If None is returned, the slice is invalid; skip to the next iteration
    if true_slice_bounds is None:
        continue
    # Otherwise, slice the image accordingly
    true_example = slice_image(*true_slice_bounds)

    # Pick a negative example outside of the positive example
    # Pick a random position outside of the range road_line_position +/- window_size
    full_image_range = set(range(320))
    # Do not center the negative example within the range of the last window
    true_example_range = set(range(*true_slice_bounds))
    # Get the elements that are in full_image_range but not in positive_example_range
    true_exclusive_example_range = full_image_range.difference(true_example_range)
    # Remove the first and last window_size elements from the set
    beginning = set(range(window_size))
    image_width = image.shape[1]
    end = set(range(image_width - window_size, image_width))
    beginning_and_end = beginning.union(end)
    false_example_range = true_exclusive_example_range.difference(beginning_and_end)
    # Choose a position randomly from the range
    false_example_position = random.choice(tuple(false_example_range))
    # Slice out the negative example centered on the random point
    false_slice_bounds = compute_slice(false_example_position)
    false_example = slice_image(*false_slice_bounds)

    # Add the images and the corresponding flags to the lists for return
    image_list.append(true_example)
    label_list.append(1)
    image_list.append(false_example)
    label_list.append(0)

# Instantiate the model and print a summary
model = get_model(window_size)
print(model.summary())
# Train the model on the data
model.fit(
    x=np.array(image_list),
    y=np.array(label_list),
    epochs=500,
    batch_size=32,
    validation_split=0.2
)
# Save the trained model
model.save(model_path)
