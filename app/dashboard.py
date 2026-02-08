import streamlit as st
import pandas as pd
import plotly.express as px
from player_stats import get_player_stats
import time

st.set_page_config(layout="wide", page_title="Chess Analyzer Dashboard")

st.title("♟️ Chess Performance Dashboard")

username = st.sidebar.text_input("Enter Chess.com Username", value="choys1211")
limit = st.sidebar.slider("Number of Games to Analyze", 5, 100, 20)
if st.sidebar.button("Fetch Data"):
    st.session_state['fetch_trigger'] = time.time()

if username:
    try:
        stats = get_player_stats(username, limit=limit)
        
        if not stats:
            st.warning("No games found or database empty for this user.")
        else:
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Win Rate", f"{stats['win_rate']}%", stats['record'])
            col2.metric("Avg Accuracy", f"{stats['avg_accuracy']}%")
            col3.metric("Play Style", stats['style'])
            col4.metric("Total Games", stats['total_games'])
            
            st.divider()
            
            history = stats['history']
            df = pd.DataFrame(history)
            
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.subheader("📈 Accuracy Trend (Last N Games)")
                if not df.empty:
                    # Sort by ID
                    df_sorted = df.sort_values(by="id")
                    fig_acc = px.line(df_sorted, x=df_sorted.index, y="accuracy", 
                                      title="Accuracy over Games", markers=True)
                    fig_acc.update_layout(xaxis_title="Game Number", yaxis_title="Accuracy %")
                    st.plotly_chart(fig_acc, use_container_width=True)
            
            with c2:
                st.subheader("🎨 Win/Loss Distribution")
                res_counts = df['result'].value_counts().reset_index()
                res_counts.columns = ['Result', 'Count']
                fig_pie = px.pie(res_counts, values='Count', names='Result', 
                                 color='Result',
                                 color_discrete_map={'Win':'#00CC96', 'Loss':'#EF553B', 'Draw':'#636EFA'})
                st.plotly_chart(fig_pie, use_container_width=True)

            c3, c4 = st.columns(2)
            
            with c3:
                st.subheader("🎯 Move Quality Breakdown")
                counts = stats['classifications']
                categories = ['Brilliant', 'Great', 'Best', 'Excellent', 'Good', 'Inaccuracy', 'Mistake', 'Blunder', 'Miss']
                
                data = [{'Category': cat, 'Count': counts.get(cat, 0)} for cat in categories]
                quality_df = pd.DataFrame(data)
                
                color_map = {
                    'Brilliant': '#1baca6', 'Great': '#99c3ff', 'Best': '#8cac8a', 
                    'Excellent': '#96c997', 'Good': '#b3d9b4', 
                    'Inaccuracy': '#f4d160', 'Miss': '#e08e79', 
                    'Mistake': '#d95f5f', 'Blunder': '#b82e2e'
                }
                
                fig_quality = px.bar(quality_df, x='Category', y='Count', 
                                     color='Category', 
                                     color_discrete_map=color_map,
                                     text='Count')
                
                # Force X-Axis Order
                fig_quality.update_layout(xaxis={'categoryorder':'array', 'categoryarray': categories}, 
                                          showlegend=False)
                st.plotly_chart(fig_quality, use_container_width=True)

            with c4:
                st.subheader("📖 Opening Performance (Currently Simulated)")
                if 'opening' in df.columns:
                    op_counts = df['opening'].value_counts().head(5)
                    st.write(op_counts)
                else: 
                     st.info("Opening data not available in this dataset yet.")
            st.divider()
            st.subheader("Recent Games Log")
            st.dataframe(df.sort_values(by="id", ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        st.info("Make sure the Database container is running (`docker-compose up -d db`).")
