from flask import Flask, render_template, request, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 업로드된 파일을 저장할 디렉토리 설정
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        # 업로드된 파일 받기
        yakga_file = request.files['yakga']
        yakguk_file = request.files['yakguk']

        if not (yakga_file and yakguk_file):
            return "심평원과 약국 파일을 모두 선택해주세요."

        # 파일 저장 및 경로 설정
        yakga_filename = secure_filename(yakga_file.filename)
        yakguk_filename = secure_filename(yakguk_file.filename)
        yakga_path = os.path.join(app.config['UPLOAD_FOLDER'], yakga_filename)
        yakguk_path = os.path.join(app.config['UPLOAD_FOLDER'], yakguk_filename)
        yakga_file.save(yakga_path)
        yakguk_file.save(yakguk_path)

        # 데이터 처리 로직
        df_yakga = pd.read_excel(yakga_path)
        df_yakguk = pd.read_excel(yakguk_path)

        fourth_column_data_yakga = df_yakga.iloc[:, 3].astype(str)
        third_column_data_yakguk = df_yakguk.iloc[:, 2].astype(str)

        matching_rows = df_yakguk[
            df_yakguk.iloc[:, 2].astype(str).isin(fourth_column_data_yakga)
        ]

        # 데이터 처리 로직에서 추가적인 부분
        g_column_index = 6
        matching_rows = matching_rows[
            matching_rows.iloc[:, g_column_index].astype(str) != "0"
        ]
        matching_rows = matching_rows[
            matching_rows.iloc[:, g_column_index].str.replace(",", "").astype(float) != 0
        ]

        # additional_df 생성
        i_column_index = 8
        j_column_index = 9
        additional_values = []

        for index, row in matching_rows.iterrows():
            fourth_column_value = row[2]
            corresponding_row_yakga = df_yakga[
                df_yakga.iloc[:, 3].astype(str) == fourth_column_value
            ]
            if not corresponding_row_yakga.empty:
                i_value = corresponding_row_yakga.iloc[0, i_column_index]
                j_value = corresponding_row_yakga.iloc[0, j_column_index] * 100
                additional_values.append([i_value, f"{int(j_value)}%"])  # 리스트 형태로 추가
            else:
                additional_values.append(["", ""])  # 리스트 형태로 추가

        # additional_df 컬럼 순서를 맞춰줌
        additional_df = pd.DataFrame(additional_values, columns=["인하후약가", "인하율"])

        # matching_rows와 additional_df를 합쳐서 result_df 생성
        result_df = pd.concat([matching_rows.reset_index(drop=True), additional_df], axis=1)

        result_df["단가"] = result_df["단가"].str.replace(",", "").astype(float)
        result_df["인하후약가"] = result_df["인하후약가"].astype(float)
        result_df["현재고"] = result_df["현재고"].str.replace(",", "").astype(float)

        result_df["차액"] = (result_df["단가"] - result_df["인하후약가"]) * result_df["현재고"]

        # 결과 파일 생성
        result_file = "yakguk_inha.xlsx"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_file)
        result_df.to_excel(result_path, index=False, engine='openpyxl')  # engine 추가

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        return f"에러 발생: {str(e)}"

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # uploads 디렉토리 생성
    app.run(debug=True)
