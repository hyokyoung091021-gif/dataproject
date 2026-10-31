import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="데이터 기초통계 분석실",
    page_icon="📊",
    layout="wide"
)

st.title("📊 데이터 기초통계 분석실")
st.write("CSV 파일의 행과 열, 결측치, 중앙값, 사분위수, 분포와 변수 간 관계를 분석합니다.")

def read_csv_safely(file):
    """여러 인코딩을 차례로 시도해 CSV를 읽습니다."""
    encodings = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]
    last_error = None
    for encoding in encodings:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=encoding, low_memory=False), encoding
        except Exception as error:
            last_error = error
    raise last_error

uploaded_file = st.file_uploader("분석할 CSV 파일을 업로드하세요.", type=["csv"])

if uploaded_file is not None:
    try:
        df, used_encoding = read_csv_safely(uploaded_file)
    except Exception as e:
        st.error(f"CSV 파일을 읽지 못했습니다: {e}")
        st.stop()
else:
    st.info("CSV 파일을 업로드하면 분석 결과가 표시됩니다.")
    st.stop()

if df.empty:
    st.warning("데이터가 비어 있습니다.")
    st.stop()

# 완전히 비어 있는 열도 포함하여 통계 계산
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

st.caption(f"파일명: {uploaded_file.name}  ·  인코딩: {used_encoding}")

# 핵심 요약
total_missing = int(df.isna().sum().sum())
duplicate_rows = int(df.duplicated().sum())
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("전체 행 수", f"{len(df):,}개")
col2.metric("전체 열 수", f"{df.shape[1]:,}개")
col3.metric("전체 결측치", f"{total_missing:,}개")
col4.metric("중복 행", f"{duplicate_rows:,}개")
col5.metric("숫자형 열", f"{len(numeric_cols):,}개")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 데이터 미리보기", "📐 기초통계", "🕳️ 결측치 분석", "📈 변수 분포", "🔗 변수 간 관계"
])

with tab1:
    st.subheader("데이터 미리보기")
    rows_to_show = st.slider("표시할 행 수", min_value=5, max_value=min(100, max(5, len(df))), value=min(10, max(5, len(df))))
    st.dataframe(df.head(rows_to_show), use_container_width=True, height=360)

    st.subheader("열 정보")
    info_df = pd.DataFrame({
        "열 이름": df.columns,
        "자료형": [str(df[c].dtype) for c in df.columns],
        "결측치 수": [int(df[c].isna().sum()) for c in df.columns],
        "고유값 수": [int(df[c].nunique(dropna=True)) for c in df.columns]
    })
    st.dataframe(info_df, use_container_width=True, hide_index=True)

    st.download_button(
        "분석 데이터 다운로드 (CSV)",
        data=df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name="분석데이터.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("숫자형 데이터의 기초통계")
    if numeric_cols:
        stats = df[numeric_cols].describe().T
        stats["중앙값"] = df[numeric_cols].median()
        stats["결측치"] = df[numeric_cols].isna().sum()
        stats = stats.rename(columns={
            "count": "개수", "mean": "평균", "std": "표준편차",
            "min": "최솟값", "25%": "1사분위수", "50%": "중앙값(50%)",
            "75%": "3사분위수", "max": "최댓값"
        })
        ordered = ["개수", "평균", "표준편차", "최솟값", "1사분위수", "중앙값(50%)", "중앙값", "3사분위수", "최댓값", "결측치"]
        stats = stats[[c for c in ordered if c in stats.columns]]
        st.dataframe(stats.style.format("{:,.2f}"), use_container_width=True)
        st.caption("중앙값은 데이터를 크기순으로 정렬했을 때 가운데에 위치하는 값입니다.")
    else:
        st.info("숫자형 열이 없습니다.")

    st.subheader("문자형 데이터의 기초통계")
    if categorical_cols:
        cat_stats = pd.DataFrame({
            "열 이름": categorical_cols,
            "개수": [int(df[c].count()) for c in categorical_cols],
            "고유값 수": [int(df[c].nunique()) for c in categorical_cols],
            "최빈값": [
                str(df[c].mode(dropna=True).iloc[0]) if not df[c].mode(dropna=True).empty else "(없음)"
                for c in categorical_cols
            ],
            "최빈값 빈도": [
                int(df[c].value_counts(dropna=True).iloc[0]) if not df[c].value_counts(dropna=True).empty else 0
                for c in categorical_cols
            ]
        })
        st.dataframe(cat_stats, use_container_width=True, hide_index=True)
    else:
        st.info("문자형 열이 없습니다.")

with tab3:
    st.subheader("열별 결측치 현황")
    missing = df.isna().sum().sort_values(ascending=False)
    missing_df = pd.DataFrame({
        "열 이름": missing.index,
        "결측치 수": missing.values,
        "결측 비율(%)": (missing.values / len(df) * 100).round(2)
    })
    st.dataframe(missing_df, use_container_width=True, hide_index=True)

    nonzero_missing = missing_df[missing_df["결측치 수"] > 0]
    if not nonzero_missing.empty:
        fig = px.bar(
            nonzero_missing.sort_values("결측치 수", ascending=True),
            x="결측치 수", y="열 이름", orientation="h",
            text="결측치 수", title="열별 결측치 개수",
            hover_data=["결측 비율(%)"]
        )
        fig.update_layout(yaxis_title="", xaxis_title="결측치 개수")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("결측치가 없습니다. 모든 열에 값이 입력되어 있습니다.")

with tab4:
    st.subheader("숫자형 변수의 분포")
    if numeric_cols:
        selected_num = st.selectbox("분포를 확인할 숫자형 열", numeric_cols)
        valid_series = df[selected_num].dropna()
        if valid_series.empty:
            st.warning("선택한 열에는 분석할 값이 없습니다.")
        else:
            a, b, c, d = st.columns(4)
            a.metric("평균", f"{valid_series.mean():,.2f}")
            b.metric("중앙값", f"{valid_series.median():,.2f}")
            c.metric("최솟값", f"{valid_series.min():,.2f}")
            d.metric("최댓값", f"{valid_series.max():,.2f}")

            left, right = st.columns(2)
            with left:
                fig_hist = px.histogram(
                    df, x=selected_num, nbins=30, marginal="box",
                    title=f"{selected_num}의 히스토그램",
                    labels={selected_num: selected_num, "count": "빈도"}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            with right:
                fig_box = px.box(df, y=selected_num, points="outliers",
                                 title=f"{selected_num}의 상자그림")
                st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("숫자형 열이 없습니다.")

    st.divider()
    st.subheader("범주형 변수의 빈도")
    if categorical_cols:
        selected_cat = st.selectbox("빈도를 확인할 문자형 열", categorical_cols)
        top_n = st.slider("표시할 범주 개수", 5, 30, 15)
        counts = df[selected_cat].fillna("(결측치)").astype(str).value_counts().head(top_n).reset_index()
        counts.columns = [selected_cat, "빈도"]
        fig_cat = px.bar(counts.sort_values("빈도"), x="빈도", y=selected_cat,
                         orientation="h", text="빈도",
                         title=f"{selected_cat}의 범주별 빈도")
        fig_cat.update_layout(yaxis_title="")
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("문자형 열이 없습니다.")

with tab5:
    st.subheader("숫자형 변수 간 상관관계")
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        fig_corr = px.imshow(
            corr, text_auto=".2f", aspect="auto",
            color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
            title="상관계수 히트맵"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        st.caption("상관계수는 두 변수의 선형적인 관계를 나타냅니다. 1에 가까우면 양의 상관, -1에 가까우면 음의 상관, 0에 가까우면 선형 관계가 약합니다.")

        x_col, y_col = st.columns(2)
        with x_col:
            x_var = st.selectbox("가로축 변수", numeric_cols, index=0)
        with y_col:
            default_y = 1 if len(numeric_cols) > 1 else 0
            y_var = st.selectbox("세로축 변수", numeric_cols, index=default_y)
        if x_var == y_var:
            st.info("서로 다른 두 변수를 선택하면 산점도에서 관계를 살펴볼 수 있습니다.")
        else:
            scatter_df = df[[x_var, y_var]].dropna()
            fig_scatter = px.scatter(scatter_df, x=x_var, y=y_var,
                                     trendline="ols",
                                     title=f"{x_var}와 {y_var}의 관계")
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("상관관계 분석에는 숫자형 열이 2개 이상 필요합니다.")

st.divider()
st.caption("※ 기초통계량은 결측치를 제외하고 계산합니다. 상관관계와 그래프도 해당 분석에 필요한 값이 있는 행을 사용합니다.")
