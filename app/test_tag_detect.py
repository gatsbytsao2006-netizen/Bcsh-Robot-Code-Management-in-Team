from sdk.api import UpAPI


if __name__ == '__main__':
    api = UpAPI()

    while True:

        find_apriltag, tag_id, offset_x = api.detect_apriltag()

        if find_apriltag:
            print(f"tag_id: {tag_id}")

            if tag_id == 1:
                api.raise_left_arm()

            elif tag_id == 3:
                api.raise_right_arm()

            elif tag_id == 5:
                api.raise_arms()

            else:
                api.put_down_arms()

        else:
            api.put_down_arms()