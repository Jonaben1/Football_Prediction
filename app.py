import streamlit as st
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import numpy as np
from scipy.stats import poisson

st.title('English Premier League 2024/2025 Prediction App')
st.write('Predict the outcome of English Premier League matches using statistical models.')


st.sidebar.markdown('Catch up with the latest Chelsea FC news at <a href="https://www.footballcatchup.com" target="_self">Football Catchup</a>', unsafe_allow_html=True)



home = st.sidebar.selectbox('Select home team', ['Arsenal', 'Aston Villa', 'Bournemouth', 'Ipswich', 'Brentford', 'Brighton', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham',
                                                 'Leicester', 'Liverpool', 'Man United', 'Man City', 'Newcastle', 'Nott\'m Forest', 'Southampton',
                                                 'Tottenham', 'West Ham', 'Wolves'])

away = st.sidebar.selectbox('Select away team', ['Aston Villa', 'Arsenal', 'Bournemouth', 'Ipswich', 'Brentford', 'Brighton', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham',
                                                 'Leicester', 'Liverpool', 'Man United', 'Man City', 'Newcastle', 'Nott\'m Forest', 'Southampton',
                                                 'Tottenham', 'West Ham', 'Wolves'])
button = st.sidebar.button('Predict')

@st.cache_data
def load_data():
    try:
        data = pd.read_csv('https://www.football-data.co.uk/mmz4281/2425/E0.csv')
        epl = data[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]
        epl = epl.rename(columns={'FTHG': 'HomeGoals', 'FTAG': 'AwayGoals'})
        home_data = epl.iloc[:, 0:3].assign(home=1).rename(columns={'HomeTeam': 'team', 'AwayTeam': 'opponent', 'HomeGoals': 'goals'})
        away_data = epl.iloc[:, [1, 0, 3]].assign(home=0).rename(columns={'AwayTeam': 'team', 'HomeTeam': 'opponent', 'AwayGoals': 'goals'})
        df = pd.concat([home_data, away_data])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

@st.cache_resource
def build_model(data):
    formula = 'goals ~ team + opponent + home'
    model = smf.glm(formula=formula, data=data, family=sm.families.Poisson()).fit()
    return model

if not df.empty:
    model = build_model(df)

    # predicting the scores
    home_goals = int(model.predict(pd.DataFrame(data={'team': home, 'opponent': away, 'home': 1}, index=[1])).iloc[0])
    away_goals = int(model.predict(pd.DataFrame(data={'team': away, 'opponent': home, 'home': 0}, index=[1])).iloc[0])
    total_goals = home_goals + away_goals

    @st.cache_resource
    def predict_match(_model, homeTeam, awayTeam, max_goals=10):
        '''Predict the odds of a home win, draw and away win returned in matrix form'''
        home_goals = _model.predict(pd.DataFrame(data={'team': homeTeam, 'opponent': awayTeam, 'home': 1}, index=[1])).values[0]
        away_goals = _model.predict(pd.DataFrame(data={'team': awayTeam, 'opponent': homeTeam, 'home': 0}, index=[1])).values[0]
        pred = [[poisson.pmf(i, team_avg) for i in range(0, max_goals + 1)] for team_avg in [home_goals, away_goals]]
        return np.outer(np.array(pred[0]), np.array(pred[1]))

    # getting the odds
    odds = predict_match(model, home, away, max_goals=total_goals)

    # odds of a home win
    home_win = np.sum(np.tril(odds, -1)) * 100
    home_win = round(home_win)
    # odds of a draw
    draw = np.sum(np.diag(odds)) * 100
    draw = round(draw)
    # odds of an away win
    away_win = np.sum(np.triu(odds, 1)) * 100
    away_win = round(away_win)

    def get_scores():
        ''' Display results'''
        # select only one team
        if home == away:
            st.error('You can\'t predict the same team')
            return None
        st.write(f'Score Prediction between {home} and {away}')
        st.write(f'{home} ------   {home_goals}:{away_goals} ------  {away}')
        st.write(f'Odds of a home win -------- {home_win}%')
        st.write(f'Odds of an away win -------  {away_win}%')
        st.write(f'Odds of a draw ---------------  {draw}%')

    if button:
        get_scores()
else:
    st.error("No data available to build the model.")

