#Google Minesweeper Easy Solver
#10/20/24

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import cv2
import numpy as np
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

#grid dimensions
x, y, width, height = (900, 337, 900, 720)
cell_size = 90 
grid_rows = 8 
grid_cols = 10 

def main():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)

    driver.get("https://g.co/kgs/uCmazF6")
    driver.maximize_window() 

    driver.implicitly_wait(2)

    playButton = driver.find_element(By.CLASS_NAME, value="fxvhbc")
    playButton.click()

    difficultySelector = driver.find_element(By.CLASS_NAME, "fHwb5b")
    difficultySelector.click()
    easyButton = driver.find_element(By.CSS_SELECTOR, "g-menu-item.EpPYLd.GZnQqe.WtV5nd") 
    easyButton.click()

    board = driver.find_element(By.CLASS_NAME, value="ecwpfc")
    board.click()
    
    boolean = True 
    screenshot_path = "webBrowser.png"
    time.sleep(2)
    while boolean:
        driver.save_screenshot(screenshot_path)
        xbutton = driver.find_element(By.ID, 'eqeexb')
        location = xbutton.location
        
        next_move = get_next_minesweeper_move("webBrowser.png")
        if next_move:
            for move in next_move:
                row, col = move
                yCoord = (row + 1) * cell_size - (cell_size/2) + y
                xCoord = (col + 1) * cell_size - (cell_size/2) + x
                actions.move_to_element_with_offset(xbutton, (xCoord/2)-location['x'], (yCoord/2)-location['y']).click().perform()
                
        else:
            print("No safe moves detected.")
            break

        source_image = cv2.imread('croppedimage.png')
        template_image = cv2.imread('WinReq.png')
        if template_match_boolean(source_image, template_image):
            boolean = False
        else:
            boolean = True
            
    print("Finished")


def template_match_boolean(image, template, threshold=0.8, method=cv2.TM_CCOEFF_NORMED):
    
    result = cv2.matchTemplate(image, template, method)
    _, max_val, _, _ = cv2.minMaxLoc(result)

    return max_val >= threshold

    
def get_next_minesweeper_move(image_path):
    image = cv2.imread(image_path)
    
    x, y, width, height = (900, 337, 900, 720)
    cell_size = 90 
    grid_rows = 8 
    grid_cols = 10 

    cropped_image = image[y:y + height, x:x + width]
    cv2.imwrite("croppedimage.png", cropped_image)

    # Dictionary to store cell contents
    board = {}

    def get_cell_content_color(cell):
        gray_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY) 
        _, thresh_cell = cv2.threshold(gray_cell, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)  
        resized_gray_cell = cv2.resize(thresh_cell, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC) 

        average_color = cv2.mean(cell)[:3] 
        
        blank_color_light = (164, 196, 224)#(229,194,159) 
        blank_color_dark = (157, 185, 210) #(215,184,153)
        unopened_color_light = (102, 214, 179)#(170,215,80) 
        unopened_color_dark = (95, 208, 172)#(162,209,72)
        
        color_threshold = 25
        # Acceptable color deviation

        extracted_text = pytesseract.image_to_string(resized_gray_cell, config='--psm 10 -c tessedit_char_whitelist=012345678')
        if bool(extracted_text.strip()):
            return extracted_text.strip() 
        elif all(abs(average_color[i] - blank_color_light[i]) < color_threshold for i in range(3)) or all(abs(average_color[j] - blank_color_dark[j]) < color_threshold for j in range(3)):
            return 'blank'
        elif all(abs(average_color[i] - unopened_color_light[i]) < color_threshold for i in range(3)) or all(abs(average_color[j] - unopened_color_dark[j]) < color_threshold for j in range(3)):
            return 'unopened'
        else:
            return "unknown"


    for row in range(grid_rows):
        for col in range(grid_cols):
            x, y = col * cell_size, row * cell_size
            cell = cropped_image[y:y+cell_size, x:x+cell_size]
            content = get_cell_content_color(cell)
            cv2.imwrite('cell.png', cell)
            board[(row, col)] = content  

    def find_next_move(board):
        next_moves = set() 

        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = [(row + dr, col + dc) 
                            for dr in [-1, 0, 1] 
                            for dc in [-1, 0, 1] 
                            if (dr, dc) != (0, 0) and (0 <= row + dr < grid_rows) and (0 <= col + dc < grid_cols)]
                
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors if board.get((nr, nc)) == 'flag')

                if len(unopened_neighbors) + flagged_neighbors == number:
                    for unopened in unopened_neighbors:
                        board[unopened] = 'flag'  

                            
        for (row, col), content in board.items():
            if content.isdigit():
                number = int(content)
                
                neighbors = [(row + dr, col + dc) 
                            for dr in [-1, 0, 1] 
                            for dc in [-1, 0, 1] 
                            if (dr, dc) != (0, 0) and (0 <= row + dr < grid_rows) and (0 <= col + dc < grid_cols)]
                
                unopened_neighbors = [(nr, nc) for (nr, nc) in neighbors if board.get((nr, nc)) == 'unopened']
                flagged_neighbors = sum(1 for (nr, nc) in neighbors if board.get((nr, nc)) == 'flag')
                
                if flagged_neighbors == number:
                    for neighbor in unopened_neighbors:
                        if board.get(neighbor) != 'flag':
                            next_moves.add(neighbor)  
            
                            

        return list(next_moves) if next_moves else None 



    return find_next_move(board)



if __name__ == "__main__":
    main()
