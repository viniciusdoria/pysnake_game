"""
Snake Game using PySDL2.

This module implements a simple Snake game using the PySDL2 library.
The snake moves around the window, eating apples to grow in size.
The game ends if the snake collides with the window boundaries or 
with itself.
"""

import json
import os
import random
import time

import sdl2
import sdl2.ext


def set_rect_color(renderer: sdl2.ext.Renderer, rect, color, fill=True):
    """
    Set the color of a rectangle and fill it using the renderer.

    Args:
        renderer (sdl2.ext.Renderer): The renderer to use for drawing.
        rect (sdl2.SDL_Rect): The rectangle to fill.
        color (tuple): The color to use for filling the rectangle (R, G, B).
        fill (bool): Whether to fill the rectangle or not.
    """

    renderer.color = sdl2.ext.Color(*color)
    renderer.draw_rect(rect, color)
    if fill is True:
        renderer.fill(rect, color)


def generate_random_position(cell_size, width, height, min_x=0, min_y=0):
    """
    Generate a random position within the window boundaries.

    Args:
        cell_size (int): The size of each cell in the grid.
        width (int): The width of the window.
        height (int): The height of the window.
        min_x (int): The minimum x-coordinate.
        min_y (int): The minimum y-coordinate.

    Returns:
        tuple: A tuple containing the x and y coordinates of the random position.
    """

    x = random.randint(min_x // cell_size, (width // cell_size) - 1) * cell_size
    y = random.randint(min_y // cell_size, (height // cell_size) - 1) * cell_size

    return min_x if x < min_x else x, min_y if y < min_y else y


def initialize_arena(renderer, width, height):

    return sdl2.SDL_Rect(
        renderer.logical_size[0] - width,
        renderer.logical_size[1] - height,
        width,
        height,
    )


def initialize_grid(cell_size, width, height, min_x=0, min_y=0):
    """
    Initialize the grid for the game.

    Args:
        cell_size (int): The size of each cell in the grid.
        width (int): The width of the window.
        height (int): The height of the window.
        min_x (int): The minimum x-coordinate.
        min_y (int): The minimum y-coordinate.

    Returns:
        list: A list of SDL_Rect objects representing the grid.
    """

    grid = []
    for x in range(min_x, width, cell_size):
        for y in range(min_y, height, cell_size):
            grid.append(sdl2.SDL_Rect(x, y, cell_size, cell_size))
    return grid


def initialize_snake(cell_size, width, height, size=3, min_x=0, min_y=0):
    """
    Initialize the snake's starting position.

    Args:
        cell_size (int): The size of each cell in the grid.
        width (int): The width of the window.
        height (int): The height of the window.
        min_x (int): The minimum x-coordinate.
        min_y (int): The minimum y-coordinate.

    Returns:
        list: A list containing the initial SDL_Rect of the snake.
    """

    snake_start_x, snake_start_y = generate_random_position(
        cell_size, width, height, min_x, min_y
    )
    return [
        sdl2.SDL_Rect(snake_start_x, snake_start_y, cell_size, cell_size)
        for _ in range(0, size)
    ]


def initialize_apple(cell_size, width, height, min_x=0, min_y=0):
    """
    Initialize the apple's starting position.

    Args:
        cell_size (int): The size of each cell in the grid.
        width (int): The width of the window.
        height (int): The height of the window.
        min_x (int): The minimum x-coordinate.
        min_y (int): The minimum y-coordinate.

    Returns:
        sdl2.SDL_Rect: The SDL_Rect representing the apple's position.
    """

    apple_x, apple_y = generate_random_position(cell_size, width, height, min_x, min_y)
    return sdl2.SDL_Rect(apple_x, apple_y, cell_size, cell_size)


def initial_direction(snake_head: sdl2.SDL_Rect, width, height):
    """
    Determine the initial direction of the snake based on its position.

    Args:
        snake (sdl2.SDL_Rect): The SDL_Rect representing the snake's head position.
        width (int): The width of the window.
        height (int): The height of the window.

    Returns:
        str: The initial direction of the snake ("UP", "DOWN", "LEFT", "RIGHT").
    """

    distances = {
        "UP": snake_head.y,
        "DOWN": height - snake_head.y,
        "LEFT": snake_head.x,
        "RIGHT": width - snake_head.x,
    }
    closest_side = min(distances, key=distances.get)
    opposite_directions = {
        "UP": "DOWN",
        "DOWN": "UP",
        "LEFT": "RIGHT",
        "RIGHT": "LEFT",
    }
    return opposite_directions[closest_side]


def render_multiline_text(
    renderer, factory, font_manager, text_lines, color, position="center"
):
    """
    Render multiline text using the renderer.

    Args:
        renderer (sdl2.ext.Renderer): The renderer to use for drawing.
        factory (sdl2.ext.SpriteFactory): The sprite factory to create text sprites.
        font_manager (sdl2.ext.FontManager): The font manager to use for text rendering.
        text (list): The text lines in a list.
        color (sdl2.ext.Color): The color of the text.
        position (text): The position relative to the renderer size to render the text.
    """

    text_position = {"x": None, "y": None, "width": None, "height": None}
    y_span = 0
    for line in text_lines:
        text_sprite = factory.from_text(line, fontmanager=font_manager, color=color)
        if position == "center":
            x = renderer.logical_size[0] / 2 - text_sprite.size[0] / 2
            y = renderer.logical_size[1] / 2 - text_sprite.size[1] / 2 + y_span
        elif position == "top_center":
            x = renderer.logical_size[0] / 2 - text_sprite.size[0] / 2
            y = 0
        elif position == "top_right":
            x = renderer.logical_size[0] - text_sprite.size[0]
            y = 0
        else:
            assert position == "top_left"
            x, y = 0, 0
        renderer.copy(
            text_sprite, dstrect=(x, y, text_sprite.size[0], text_sprite.size[1])
        )
        # Move y-coordinate down for the next line
        y_span += text_sprite.size[1]

        if text_position["x"] is None:
            text_position["x"] = x
            text_position["y"] = y
        text_position["width"] = text_sprite.size[0]
        text_position["height"] = y_span

    renderer.present()

    return text_position


def log_record(record, snake_size):
    """
    Update the record if the current snake size is greater than the record.

    Args:
        record (int): The current record size.
        snake_size (int): The current snake size.

    Returns:
        int: The updated record size.
    """

    if snake_size > record:
        record = snake_size
        data = {"record": record}
        with open("resources/data.json", "w") as file:
            json.dump(data, file)
    return record


def event_exit(event):
    """
    Check if the event is an exit event (quit or escape key).

    Args:
        event (sdl2.SDL_Event): The SDL event to check.

    Returns:
        bool: True if the event is an exit event, False otherwise.
    """

    result = event.type == sdl2.SDL_QUIT or event.key.keysym.sym == sdl2.SDLK_ESCAPE
    return result


def format_time(seconds):
    """
    Format the time in seconds to mm:ss format.

    Args:
        seconds (int): The time in seconds.

    Returns:
        str: The formatted time in mm:ss format.
    """
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"


def main():
    """
    Main function to run the Snake game.
    """

    # Initial game set up
    resources_path = os.path.join(os.path.dirname(__file__), "resources")
    record = json.load(open(os.path.join(resources_path, "data.json")))
    record = record["record"]

    # Set window and cell sizes
    window_width = 250
    window_height = 200
    status_height = 30
    cell_size = 10

    # Initialize snake attributes
    snake_colors = [
        (248, 80, 8),
        (255, 242, 172),
        (0, 0, 0),
        (255, 242, 172),
        (248, 80, 8),
    ]
    snake_initial_size = 3

    # Color of the apple
    apple_color = (0, 255, 0)

    # Bakcground color
    background_color = (111, 111, 111)

    # Initialize SDL
    sdl2.ext.init()

    # Create and show the window
    window = sdl2.ext.Window("pySnake Game", size=(window_width, window_height))
    window.show()

    # Get surface to draw on
    window_renderer = sdl2.ext.Renderer(window)

    # Create a sprite factory
    factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=window_renderer)

    # Default font manager
    font_manager = sdl2.ext.FontManager(
        os.path.join(resources_path, "OpenSans-Bold.ttf")
    )

    # Default font color
    font_color = sdl2.ext.Color(0, 255, 0)

    # Initialize snake and apple positions
    snake = initialize_snake(
        cell_size, window_width, window_height, snake_initial_size, min_y=status_height
    )
    apple_rect = initialize_apple(
        cell_size, window_width, window_height, min_y=status_height
    )

    # Create a grid for the game
    grid_color = (50, 50, 50)
    grid = initialize_grid(cell_size, window_width, window_height, min_y=status_height)

    # Create a boundary for the arena area
    arena_boundary = initialize_arena(
        window_renderer, window_width, window_height - status_height
    )

    # Set the initial direction of the snake
    direction = initial_direction(snake[0], window_width, window_height)

    running = True
    paused = False
    start_time = time.time()
    total_paused_time = 0
    pause_start_time = 0

    while running is True:
        # Set default delay to control the speed of the snake
        delay_time = 200

        # Check if key is pressed to change the speed of the snake
        key_scancodes = {
            sdl2.SDL_SCANCODE_UP: "UP",
            sdl2.SDL_SCANCODE_DOWN: "DOWN",
            sdl2.SDL_SCANCODE_LEFT: "LEFT",
            sdl2.SDL_SCANCODE_RIGHT: "RIGHT",
        }
        keystates = sdl2.SDL_GetKeyboardState(None)
        if any(
            keystates[key_state] and key_direction == direction
            for key_state, key_direction in key_scancodes.items()
        ):
            delay_time = 50

        for event in sdl2.ext.get_events():
            running = not event_exit(event)
            if running is False:
                break

            # Check for space key to pause the game
            if (
                event.type == sdl2.SDL_KEYDOWN
                and event.key.keysym.sym == sdl2.SDLK_SPACE
            ):
                paused = True
                pause_start_time = time.time()

                # Show pouse text
                text_lines = ["Game Paused.", "Press any arrow key to continue."]
                render_multiline_text(
                    window_renderer,
                    factory,
                    font_manager,
                    text_lines,
                    font_color,
                    "center",
                )

                while paused is True:
                    sdl2.SDL_Delay(10)
                    for event in sdl2.ext.get_events():
                        running = not event_exit(event)
                        if running is False:
                            paused = False
                            break
                        if any(
                            event.key.keysym.sym == key
                            for key in [
                                sdl2.SDLK_UP,
                                sdl2.SDLK_DOWN,
                                sdl2.SDLK_LEFT,
                                sdl2.SDLK_RIGHT,
                            ]
                        ):
                            paused = False
                            total_paused_time += time.time() - pause_start_time
                            break

            # Change the direction of the snake based on the key pressed
            if event.key.keysym.sym == sdl2.SDLK_UP and direction != "DOWN":
                direction = "UP"
            elif event.key.keysym.sym == sdl2.SDLK_DOWN and direction != "UP":
                direction = "DOWN"
            elif event.key.keysym.sym == sdl2.SDLK_LEFT and direction != "RIGHT":
                direction = "LEFT"
            elif event.key.keysym.sym == sdl2.SDLK_RIGHT and direction != "LEFT":
                direction = "RIGHT"

        # Update the snake's position based on the current direction
        head = snake[0]
        new_head = sdl2.SDL_Rect(head.x, head.y, cell_size, cell_size)
        if direction == "UP":
            new_head.y -= cell_size
        elif direction == "DOWN":
            new_head.y += cell_size
        elif direction == "LEFT":
            new_head.x -= cell_size
        elif direction == "RIGHT":
            new_head.x += cell_size

        # Check for collision with the apple
        if new_head.x == apple_rect.x and new_head.y == apple_rect.y:
            apple_rect = initialize_apple(
                cell_size, window_width, window_height, min_y=status_height
            )
            # Chck if there are free cells to add a new apple
            if len(snake) < len(grid):
                # Check if the apple is not on the snake
                while any(
                    segment.x == apple_rect.x and segment.y == apple_rect.y
                    for segment in snake
                ):
                    apple_rect = initialize_apple(
                        cell_size, window_width, window_height, min_y=status_height
                    )
            else:
                # If there are no free cells, the game is won
                text_lines = [
                    "Congratulations! You have won the game.",
                    "Click here or press enter key to restart the game.",
                ]
                text_position = render_multiline_text(
                    window_renderer,
                    factory,
                    font_manager,
                    text_lines,
                    font_color,
                    "center",
                )

                # Update the record if neededs
                record = log_record(record, len(snake))

                # Check selection
                restart = False
                while running is True:
                    for event in sdl2.ext.get_events():
                        running = not event_exit(event)
                        if running is False:
                            break
                        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                            x, y = event.button.x, event.button.y
                            if (
                                text_position["x"]
                                <= x
                                <= text_position["x"] + text_position["width"]
                                and text_position["y"]
                                <= y
                                <= text_position["y"] + text_position["height"]
                            ):
                                running = False
                                restart = True
                                break
                            # if any(
                            #     event.key.keysym.sym == key
                            #     for key in [
                            #         sdl2.SDLK_UP,
                            #         sdl2.SDLK_DOWN,
                            #         sdl2.SDLK_LEFT,
                            #         sdl2.SDLK_RIGHT,
                            #     ]
                            # ):
                        if event.key.keysym.sym == sdl2.SDLK_RETURN:
                            running = False
                            restart = True
                            break

                    # Add a delay to reduce CPU usage
                    sdl2.SDL_Delay(10)

                if restart is True:
                    running = True
                    snake = initialize_snake(
                        cell_size,
                        window_width,
                        window_height,
                        snake_initial_size,
                        min_y=status_height,
                    )
                    apple_rect = initialize_apple(
                        cell_size, window_width, window_height, min_y=status_height
                    )
                    direction = initial_direction(snake[0], window_width, window_height)
                    start_time = time.time()
                    elapsed_time = 0
                    total_paused_time = 0
                continue
        else:
            snake.pop()  # Remove the last segment if no apple is eaten

        # Add the new head to the snake
        snake.insert(0, new_head)

        # Update snake size
        snake_size = len(snake)

        # Check for collision with itself
        snake_collision = any(
            segment.x == new_head.x and segment.y == new_head.y for segment in snake[1:]
        )

        # Check for collision with the window boundaries
        window_collision = (
            new_head.x < 0
            or new_head.x >= window_width
            or new_head.y < status_height
            or new_head.y >= window_height
        )

        if snake_collision or window_collision:
            # Update the record if neededs
            record = log_record(record, snake_size)

            # Show game over and option to restart the game
            # Refresh the window to show the changes
            window_renderer.present()

            # Create a text sprite
            text_lines = [
                "Game Over! Click here or press",
                "enter key to restart the game.",
            ]
            text_position = render_multiline_text(
                window_renderer,
                factory,
                font_manager,
                text_lines,
                font_color,
                "center",
            )

            # Check selection
            restart = False
            while running is True:
                for event in sdl2.ext.get_events():
                    running = not event_exit(event)
                    if running is False:
                        break
                    if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                        x, y = event.button.x, event.button.y
                        if (
                            text_position["x"]
                            <= x
                            <= text_position["x"] + text_position["width"]
                            and text_position["y"]
                            <= y
                            <= text_position["y"] + text_position["height"]
                        ):
                            running = False
                            restart = True
                            break
                    # if any(
                    #     event.key.keysym.sym == key
                    #     for key in [
                    #         sdl2.SDLK_UP,
                    #         sdl2.SDLK_DOWN,
                    #         sdl2.SDLK_LEFT,
                    #         sdl2.SDLK_RIGHT,
                    #     ]
                    # ):
                    if event.key.keysym.sym == sdl2.SDLK_RETURN:
                        running = False
                        restart = True
                        break

                # Add a delay to reduce CPU usage
                sdl2.SDL_Delay(10)

            if restart is True:
                running = True
                snake = initialize_snake(
                    cell_size,
                    window_width,
                    window_height,
                    snake_initial_size,
                    min_y=status_height,
                )
                apple_rect = initialize_apple(
                    cell_size, window_width, window_height, min_y=status_height
                )
                direction = initial_direction(snake[0], window_width, window_height)
                start_time = time.time()
                elapsed_time = 0

        # Clear the window surface
        window_renderer.clear(sdl2.ext.Color(*background_color))

        # Redraw the snake and apple
        for idx, segment in enumerate(snake):
            if idx <= 1:
                segment_color = snake_colors[2]
            else:
                segment_color = snake_colors[
                    snake.index(segment) % len(snake_colors) - 2
                ]
            set_rect_color(window_renderer, segment, segment_color)
        set_rect_color(window_renderer, apple_rect, apple_color)

        # Render the grid
        for cell in grid:
            set_rect_color(window_renderer, cell, background_color, False)

        # Render the arena boundary
        set_rect_color(window_renderer, arena_boundary, grid_color, False)

        # Render the elapsed time
        elapsed_time = time.time() - start_time - total_paused_time
        time_text = format_time(int(elapsed_time))
        render_multiline_text(
            window_renderer,
            factory,
            font_manager,
            [time_text],
            font_color,
            position="top_center",
        )

        # Render apples eaten
        apples_text = f"Apples: {snake_size - snake_initial_size}"
        render_multiline_text(
            window_renderer,
            factory,
            font_manager,
            [apples_text],
            font_color,
            position="top_left",
        )

        # Render all-time record
        record_text = f"Record: {record}"
        render_multiline_text(
            window_renderer,
            factory,
            font_manager,
            [record_text],
            font_color,
            position="top_right",
        )

        # Refresh the window to show the changes
        window_renderer.present()

        # print(delay_time)
        sdl2.SDL_Delay(delay_time)

    sdl2.ext.quit()


if __name__ == "__main__":
    main()
