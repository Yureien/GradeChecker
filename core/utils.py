from io import BytesIO
import typing as t
from datetime import date

from PIL import Image
from bs4 import BeautifulSoup
import numpy as np
import cv2
import pytesseract
import requests

if __name__ == "__main__":
    import sys
    import datetime
    import json
    from errors import (
        ParseException,
        UnknownException,
        AuthenticationException,
        CaptchaException,
    )
else:
    from core.errors import (
        ParseException,
        UnknownException,
        AuthenticationException,
        CaptchaException,
    )


PYTESSERACT_CONFIG = "-l eng --psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CAPTCHA_SOLVE_ATTEMPTS = 3


def get_data(roll_number: str, date_of_birth: date) -> t.Dict[str, t.Any]:
    session, content = authenticate(roll_number, date_of_birth)
    if not session:
        raise UnknownException("No idea ¯\_(ツ)_/¯")

    year = 2000 + int(roll_number[:2])

    data = {"semesters": [], "year": year}

    soup = BeautifulSoup(content, "html.parser")
    data_list = soup.find_all("input", {"type": "hidden"})
    for item in data_list:
        id = item.get("id")
        value = item.get("value")
        if not item or not value:
            continue
        if id == "name":
            data["name"] = value.strip()
        if id == "coursename":
            data["course"] = value.strip()

    subjects = {}
    resp = session.post(
        f"https://erp.iitkgp.ac.in/StudentPerformanceV2/secure/Stud_Performance.htm?rollno={roll_number}&disp_val=A"
    )
    try:
        resp_data = resp.json()
        for subject in resp_data:
            if subject["ltp"]:
                ltp = [int(i.strip()) for i in subject["ltp"].split("-")]
            else:
                ltp = [0, 0, 0]
            sem_no = int(subject["semno"])
            sem_data = {
                "code": subject["subno"],
                "name": subject["subname"],
                "credits": int(subject["crd"] if subject["crd"] else 0),
                "lectures": ltp[0],
                "tutorials": ltp[1],
                "practicals": ltp[2],
                "sub_type": subject["sub_type"],
                "grade": subject["grade"],
            }
            if sem_no not in subjects:
                subjects[sem_no] = []
            subjects[sem_no].append(sem_data)
    except (ValueError, KeyError, IndexError):
        raise ParseException("Could not parse data")

    resp = session.post(
        f"https://erp.iitkgp.ac.in/StudentPerformanceV2/secure/StudentPerfDtls.htm?rollno={roll_number}"
    )
    try:
        resp_data = resp.json()
        for semester in resp_data:
            sctscc = [int(i.strip()) for i in semester["sctscc"].split("-")]
            tcttcc = [int(i.strip()) for i in semester["tcttcc"].split("-")]
            asctascc = [int(i.strip()) for i in semester["asctascc"].split("-")]
            atctatcc = [int(i.strip()) for i in semester["atctatcc"].split("-")]
            nccgsg = [float(i.strip()) for i in semester["nccgsg"].split("-")]
            acgasg = [float(i.strip()) for i in semester["acgasg"].split("-")]
            sem_no = int(semester["semno"])
            sem_year = year + (sem_no - 1) // 2
            period = (sem_no % 2) + 1
            sem_data = {
                "year": sem_year,
                "period": period,
                "number": sem_no,
                "credits_taken": sctscc[0],
                "credits_cleared": sctscc[1],
                "total_credits_taken": tcttcc[0],
                "total_credits_cleared": tcttcc[1],
                "addn_credits_taken": asctascc[0],
                "addn_credits_cleared": asctascc[1],
                "addn_total_credits_taken": atctatcc[0],
                "addn_total_credits_cleared": atctatcc[1],
                "ncgpa": nccgsg[0],
                "cgpa": nccgsg[1],
                "sgpa": nccgsg[2],
                "acgpa": acgasg[0],
                "asgpa": acgasg[1],
                "subjects": subjects[sem_no],
            }
            data["semesters"].append(sem_data)
        data["cgpa"] = data["semesters"][-1]["cgpa"]
        data["acgpa"] = data["semesters"][-1]["acgpa"]
    except (ValueError, KeyError, IndexError):
        raise ParseException("Could not parse data")

    return data


def test_credentials(roll_number: str, date_of_birth: date) -> bool:
    try:
        authenticate(roll_number, date_of_birth)
    except AuthenticationException:
        return False

    return True


def authenticate(
    roll_number: str, date_of_birth: date
) -> t.Optional[t.Tuple[requests.Session, str]]:
    session = requests.Session()
    resp = session.get("https://erp.iitkgp.ac.in/StudentPerformanceV2/auth/login.htm")
    if resp.status_code not in [200, 302]:
        return

    retries = 0
    while retries < CAPTCHA_SOLVE_ATTEMPTS:
        resp = session.get(
            "https://erp.iitkgp.ac.in/StudentPerformanceV2/auth/getCaptchaCode.htm"
        )
        if resp.status_code not in [200, 302]:
            return

        captcha_code = resp.text
        captcha_text = solve_captcha_from_code(captcha_code)

        data = {
            "rollno": roll_number,
            "dob": date_of_birth.strftime("%d-%m-%Y"),
            "passline": captcha_text,
        }

        resp = session.post(
            "https://erp.iitkgp.ac.in/StudentPerformanceV2/auth/authenticate.htm",
            data=data,
        )
        content = resp.text

        if (
            "<br> The Captcha Code Should Be" in content
            or "<br> The Captcha Code Is Incorrect" in content
        ):
            retries += 1
            continue

        if "Roll No.,Date of Birth does not match" in content:
            raise AuthenticationException("Invalid Roll Number/Date of Birth")

        if "<title>Students Details page</title>" not in content:
            raise UnknownException("No idea ¯\_(ツ)_/¯")

        break
    else:
        raise CaptchaException("Failed to solve captcha")

    return session, content


def solve_captcha_from_code(code: str) -> str:
    url = f"https://erp.iitkgp.ac.in/StudentPerformanceV2/auth/PassImageServlet/{code}"
    response = requests.get(url)
    bytes_stream = BytesIO(response.content)
    image = Image.open(bytes_stream)
    text = solve_captcha(image)
    image.close()
    bytes_stream.close()
    return text


def solve_captcha(image: Image) -> str:
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Preprocessing
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.bitwise_not(img)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (150, 1))
    hor_det_lines = cv2.morphologyEx(
        img, cv2.MORPH_OPEN, horizontal_kernel, iterations=1
    )

    cnts = cv2.findContours(hor_det_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(img, [c], -1, (0, 0, 0), 1)

    repair_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, repair_kernel, iterations=1)

    # Remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    ver_det_lines = cv2.morphologyEx(img, cv2.MORPH_OPEN, vertical_kernel, iterations=1)

    cnts = cv2.findContours(ver_det_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(img, [c], -1, (0, 0, 0), 1)

    repair_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
    img = 255 - cv2.morphologyEx(img, cv2.MORPH_CLOSE, repair_kernel, iterations=1)

    pil_img = Image.fromarray(img)
    string = pytesseract.image_to_string(pil_img, config=PYTESSERACT_CONFIG, lang="eng")
    pil_img.close()

    string = string.strip().replace(" ", "")
    return string


if __name__ == "__main__":
    dob = datetime.datetime.strptime(sys.argv[2], "%d-%m-%Y")
    # print(test_credentials(sys.argv[1], dob))
    print(json.dumps(get_data(sys.argv[1], dob), indent=4))
