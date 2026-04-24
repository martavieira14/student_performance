from shiny import App, req, ui, render, reactive
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
import seaborn as sns
import scipy.stats as stats
import io

# UI
app_ui = ui.page_fluid(
    ui.h2("Student Insights & Analysis"),
    
    ui.navset_card_pill(
          # Data Overview Tab
          ui.nav_panel("Data Overview",
            ui.card(
                ui.input_file("my_file", "Upload CSV file", accept=[".csv"]),
                ui.hr(),
                ui.h4("Dataset Information:"),
                ui.output_text_verbatim("info"),
                ui.hr(),
                ui.h4("Data Preview (Top 5 rows):"),
                ui.output_table("head_table", style="overflow-x: auto;")
            )
        ),

        # Missing Values Tab
        ui.nav_panel("Missing Values",
            ui.card(
                ui.h4("Managing Missing Values"),
                ui.row(
                    ui.column(4, ui.input_select("na_col", "Select Column with NAs:", choices=[])),
                    ui.column(4, ui.output_ui("na_method_ui")), 
                    ui.column(4, ui.br(), ui.input_task_button("btn_apply_na", "Apply Fix", class_="btn-warning"))
                ),
                ui.hr(),
                ui.output_text("na_status"),
                ui.div(ui.output_table("head_table_clean"), style="overflow-x: auto;"),
                ui.card_footer(
                    ui.download_button("download_clean_csv", "Download Cleaned CSV", class_="btn-success")
                )
            )
        ),

        # Statistics Tab
        ui.nav_panel("Statistics",
            ui.card(
                ui.h4("Configuration:"),
                ui.row(
                    ui.column(6, ui.input_select("target_col", "Choose the dependent variable (Target):", choices=[])),
                    ui.column(6, ui.input_slider("percent", "Top/Bottom % to analyze:", 1, 50, 10))
                ),
                ui.hr(),
                ui.h4("Descriptive Analysis"),
                ui.output_table("stats_descriptive", style="overflow-x: auto;"),
                ui.hr(),
                
                ui.h4(ui.output_text("dynamic_stats_title")),
                ui.row(
                    ui.column(6, ui.h5("Top Group Mean/Mode"), ui.output_table("top_group_stats")),
                    ui.column(6, ui.h5("Bottom Group Mean/Mode"), ui.output_table("bottom_group_stats"))
                ),
                ui.hr(),

                ui.h4("Correlation with Target"),
                ui.output_text_verbatim("corr_analysis"),
                ui.hr(),
                ui.card_footer(
                    ui.download_button("download_stats_report", "Download Statistics Report (.txt)", class_="btn-success")
                )
            )
        ),

        # Visualizations Tab
        ui.nav_panel("Visualizations",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Graph Configuration"),
                    ui.input_select("viz_type", "Type of Analysis:", 
                                   choices={"uni": "Univariate", "bi": "Bivariate", "multi": "Correlation Heatmap"}),
                    
                    ui.panel_conditional("input.viz_type != 'multi'", ui.input_select("viz_x", "Variable X:", choices=[])),
                    ui.output_ui("dynamic_viz_options")
                ),
                ui.card(
                    ui.output_plot("main_plot", height="600px")
                )
            )
        )
    ))

# Server   
def server(input, output, session):
    dataset = reactive.Value(None)

    # Load and process the uploaded CSV file
    @reactive.Effect
    @reactive.event(input.my_file) 
    def load_data():
        file = input.my_file()
        try:
            df = pd.read_csv(file[0]["datapath"])
            dataset.set(df)
            cols = list(df.columns)

            cols_with_nas = df.columns[df.isnull().any()].tolist()
            ui.update_select("na_col", choices=cols_with_nas)

            ui.update_select("target_col", choices=cols)
            ui.update_select("viz_x", choices=cols)

        except Exception as e:
            ui.notification_show("Invalid or corrupted CSV file.", type="error")
            return
    
    # NA handling based on column type and presence of NAs
    @output
    @render.ui
    def na_method_ui():
        df = dataset.get()
        req(df is not None)
        col = input.na_col()
        if col in df.columns:
            if df[col].isnull().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    return ui.input_select("na_method", "Method:", choices={"mean": "Mean", "median": "Median", "drop": "Drop Rows"})
                else:
                    return ui.input_select("na_method", "Method:", choices={"mode": "Mode", "drop": "Drop Rows"})
        return ui.p("Done!")

    # Apply NA fix and update dataset
    @reactive.Effect
    @reactive.event(input.btn_apply_na)
    def apply_na_fix():
        df = dataset.get()
        req(df is not None)
        
        new_df = df.copy()
        col = input.na_col()
        method = input.na_method() if "na_method" in input else None
        if method is None: return
        
        if col and col in new_df.columns:
            if method == "mean":
                new_df[col] = new_df[col].fillna(new_df[col].mean())
            elif method == "median":
                new_df[col] = new_df[col].fillna(new_df[col].median())
            elif method == "mode":
                mode = new_df[col].mode()
                if mode.empty:
                    return  
                new_df[col] = new_df[col].fillna(mode[0])
            elif method == "drop":
                new_df = new_df.dropna(subset=[col])
            
            dataset.set(new_df)
            
            remaining_nas = new_df.columns[new_df.isnull().any()].tolist()
            ui.update_select("na_col", choices=remaining_nas if remaining_nas else ["No NAs remaining"])
            
            ui.notification_show(f"Processed {col}!", type="message")

    # Dynamic title for group analysis based on selected target and percentage
    @output
    @render.text
    def dynamic_stats_title():
        return f"Group Analysis (Top/Bottom {input.percent()}%)"

    def get_group_stats(df, target, percent, get_top=True):
        if df is None or target not in df.columns: return None
        if not pd.api.types.is_numeric_dtype(df[target]): return pd.DataFrame({"Error": ["Target must be numeric"]})
        n = max(1, int(len(df) * (percent / 100)))
        group = df.nlargest(n, target) if get_top else df.nsmallest(n, target)
        
        stats_list = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats_list.append({"Variable": col, "Value": round(group[col].mean(), 2), "Type": "Mean"})
            else:
                mode_val = group[col].mode()
                val = mode_val[0] if not mode_val.empty else "N/A"
                stats_list.append({"Variable": col, "Value": val, "Type": "Mode"})
        return pd.DataFrame(stats_list)
    
    # Generate group stats for top segment
    @output
    @render.table
    def top_group_stats():
        return get_group_stats(dataset.get(), input.target_col(), input.percent(), True)

    # Generate group stats for bottom segment
    @output
    @render.table
    def bottom_group_stats():
        return get_group_stats(dataset.get(), input.target_col(), input.percent(), False)

    # Create a comprehensive statistics report for download
    @render.download(filename="stats_report.txt")
    def download_stats_report():
        df = dataset.get()
        req(df is not None)
        target = input.target_col()
        percent = input.percent()
        
        with io.StringIO() as buf:
            buf.write("=== DATASET STATISTICS REPORT ===\n\n")
            buf.write(f"Rows: {df.shape[0]} | Cols: {df.shape[1]}\n")
            buf.write(f"Remaining Missing Values (NAs): {df.isna().sum().sum()}\n\n")
            
            buf.write("--- DESCRIPTIVE STATS ---\n")
            buf.write(df.describe().to_string())
            buf.write("\n\n")
                
            if target in df.columns:
                buf.write(f"--- GROUP ANALYSIS (TOP & BOTTOM {percent}% based on '{target}') ---\n\n")
                top_df = get_group_stats(df, target, percent, True)
                bot_df = get_group_stats(df, target, percent, False)
                    
                buf.write(f">> TOP {percent}% PROFILE:\n")
                if top_df is not None: buf.write(top_df.to_string(index=False))
                buf.write("\n\n")
                    
                buf.write(f">> BOTTOM {percent}% PROFILE:\n")
                if bot_df is not None: buf.write(bot_df.to_string(index=False))
                buf.write("\n\n")
                
            buf.write("--- CORRELATIONS WITH TARGET ---\n")
            if target in df.columns and pd.api.types.is_numeric_dtype(df[target]):
                buf.write(df.select_dtypes(include=[np.number]).corr()[target].sort_values(ascending=False).to_string())
            else:
                buf.write("No numeric target selected or invalid target for correlation.")
                    
            yield buf.getvalue()

    # Visualization options based on selected analysis type and variable
    @output
    @render.ui
    def dynamic_viz_options():
        df = dataset.get()
        mode = input.viz_type()
        x = input.viz_x()
        
        if df is None or not x: return ui.p("Please upload a dataset first.", style="color: #d9534f; font-weight: bold;")


        if mode == "uni":
            if pd.api.types.is_numeric_dtype(df[x]):
                return ui.input_select("style", "Plot Style:", choices={"hist": "Histogram", "qq": "Q-Q Plot", "box": "Boxplot"})
            else:
                return ui.input_select("style", "Plot Style:", choices={"bar": "Bar Chart", "pie": "Pie Chart"})
        
        elif mode == "bi":
            cols = list(df.columns)
            return ui.TagList(
                ui.input_select("viz_y", "Variable Y:", choices=cols),
                ui.p("Chart type auto-adapts to data types.")
            )
        
        elif mode == "multi":
            return ui.p("Numeric variables will be used automatically.")

    # Main plotting function that adapts to the selected visualization type and variables
    @output
    @render.plot
    def main_plot():
        df = dataset.get()
        fig = Figure(figsize=(10, 6))
        ax = fig.subplots()
        mode = input.viz_type()
        x = input.viz_x()
        
        if df is None:
            ax.text(0.5, 0.5, 'No dataset loaded.\nPlease upload a CSV file in the "Data Overview" tab.',
                    ha='center', va='center', fontsize=14, color='gray')
            ax.axis('off')
            return fig

        if mode == "multi":
            num_df = df.select_dtypes(include=[np.number])
            if not num_df.empty:
                if num_df.shape[1] > 20:
                    ax.text(0.5, 0.5, 'Too many variables for the heatmap (>20).', 
                            ha='center', va='center', fontsize=12, color='red')
                    ax.axis('off')
                else:
                    sns.heatmap(num_df.corr(), annot=True, cmap="coolwarm", ax=ax)
            else:
                ax.text(0.5, 0.5, 'No numeric variables available for heatmap.', ha='center', va='center')
                ax.axis('off')

        elif mode == "uni":
            style = input.style()
            if pd.api.types.is_numeric_dtype(df[x]):
                if style == "hist": sns.histplot(df[x], kde=True, ax=ax, color="palevioletred")
                elif style == "qq": stats.probplot(df[x].dropna(), dist="norm", plot=ax)
                elif style == "box": sns.boxplot(y=df[x], ax=ax, color="coral")
            else:
                if style == "bar": sns.countplot(data=df, x=x, ax=ax, color="mediumseagreen")
                elif style == "pie": df[x].value_counts().plot.pie(autopct='%1.1f%%', ax=ax, colors=sns.color_palette("pastel"), startangle=90, counterclock=False)

        elif mode == "bi":
            y = input.viz_y()
            is_x_num = pd.api.types.is_numeric_dtype(df[x])
            is_y_num = pd.api.types.is_numeric_dtype(df[y])
            
            if is_x_num and is_y_num:
                sns.regplot(data=df, x=x, y=y, ax=ax, color="steelblue", line_kws={"color": "red"})
            elif (not is_x_num and is_y_num) or (is_x_num and not is_y_num):
                sns.boxplot(data=df, x=x, y=y, ax=ax, color="coral")
            else:
                pd.crosstab(df[x], df[y]).plot(kind="bar", stacked=True, ax=ax, color=["lightcoral", "lightskyblue"])
        
        fig.tight_layout()
        return fig
    
    # Dataset information and summary statistics
    @output
    @render.text
    def info():
        df = dataset.get()
        if df is None: return "No dataset loaded."
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        total_nas = df.isna().sum().sum()
        percentage_na = (total_nas / df.size) * 100 if df.size > 0 else 0
        return (f"Rows: {df.shape[0]} | Columns: {df.shape[1]}\n"
                f"Numeric Variables: {len(num_cols)} | Categorical Variables: {len(cat_cols)}\n"
                f"Missing Values: {total_nas} ({percentage_na:.2f}%)")

    # Data preview (top 5 rows) 
    @output
    @render.table
    def head_table():
        df = dataset.get()
        req(df is not None)
        return df.head(5)

    # Descriptive statistics for numeric variables
    @output
    @render.table
    def stats_descriptive():
        df = dataset.get()
        req(df is not None)
        return df.describe().reset_index()
    
    # Status of missing values after applying fixes
    @output
    @render.text
    def na_status():
        df = dataset.get()
        req(df is not None)
        return f"Dataset contains currently {df.isna().sum().sum()} missing values." 

    # Cleaned data preview after NA handling
    @output
    @render.table
    def head_table_clean():
        df = dataset.get()
        req(df is not None)
        return df.head(5)

    # Correlation analysis of numeric variables with the selected target variable
    @output
    @render.text
    def corr_analysis():
        df = dataset.get()
        req(df is not None)
        target = input.target_col()
        if target in df.columns and pd.api.types.is_numeric_dtype(df[target]):
            return str(df.select_dtypes(include=[np.number]).corr()[target].sort_values(ascending=False))
        return "Select a numeric target."
    
    # Download the cleaned dataset as a CSV file
    @render.download(filename="cleaned_dataset.csv")
    def download_clean_csv():
        df = dataset.get()
        if df is not None:
            yield df.to_csv(index=False)

app = App(app_ui, server)