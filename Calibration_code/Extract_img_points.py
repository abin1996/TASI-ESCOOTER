import cv2

def select_points(image_path):
    # Load the image
    img = cv2.imread(image_path)
    
    # Resize image to fit within screen size
    screen_height, screen_width = 1080, 1920  # Adjust these values according to your screen resolution
    img_height, img_width = img.shape[:2]
    if img_height > screen_height or img_width > screen_width:
        scaling_factor = min(screen_height / img_height, screen_width / img_width)
        img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    
    img_copy = img.copy()
    points = []

    def mouse_callback(event, x, y, flags, param):
        nonlocal points

        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 8: # You can change the max limits here
                cv2.circle(img_copy, (x, y), 3, (0, 255, 0), -1)
                cv2.putText(img_copy, f"img_pt_{len(points) + 1}", (x + 5, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                points.append((x, y))
                cv2.imshow('image', img_copy)

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)  # Create resizable window
    cv2.setMouseCallback('image', mouse_callback)

    while True:
        cv2.imshow('image', img_copy)
        key = cv2.waitKey(1) & 0xFF

        # If 'enter' is pressed, exit loop
        if key == 13:  # ASCII code for Enter key
            break

    cv2.destroyAllWindows()

    return points

# Provide the path of the image below
# Select the points; Max limit is 8 (Change it above in the code)
# Press enter to close the window
selected_points = select_points('your_img_path')
print("Selected points:", selected_points)
