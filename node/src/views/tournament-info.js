/* global $ React ReactDOM:true */
var TournamentInfo = React.createClass({
    propTypes: {
        name: React.PropTypes.string.isRequired,
        entries: React.PropTypes.Number,
        date: React.PropTypes.string
    },
    render: function() {
        return (
            <div>
                <ul>
                    <li>Name: {this.props.name}</li>
                    <li>Date: {this.props.date || "N/A"}</li>
                    <li>Confirmed Entries: {this.props.entries || 0}</li>
                </ul>
            </div>
        );
    }
});

var TournamentInfoPage = React.createClass({
    getInitialState: function() {
        return ({successText: "", error: ""});
    },
    componentDidMount: function() {
        this.serverRequest = $.get(window.location + "/content",
            function (result) {
                this.setState(result);
            }.bind(this));
    },
    componentWillUnmount: function() {
        this.serverRequest.abort();
    },
    handleSubmit: function(e) {
        // you are the devil! This controller crap should be in a separate file.
        e.preventDefault();
        var _this = this,
            tournament = $("input#tournament").val();

        var checkRedirect = function(xhr) {
            if (xhr.responseText && typeof xhr.responseJSON === "undefined") {
                var newDoc = document.open("text/html", "replace");
                newDoc.write(xhr.responseText);
                newDoc.close();
                window.location.replace("/login?next=" + window.location.href);
                return true;
            }
            return false;
        }

        $.post(window.location, { tournament: tournament})
            .done(function (res, status, xhr) {
                if (checkRedirect(xhr)) {
                    return false;
                }
                else {
                    _this.setState({
                        successText: xhr.responseJSON.message,
                        error: ""
                    });
                }
            })
            .fail(function (res) {
                _this.setState(res.responseJSON);
            });
    },
    render: function() {

        var infoWidget = this.state.name && !this.state.successText ?
                 <TournamentInfo name={this.state.name}
                                 entries={this.state.entries}
                                 date={this.state.date} />
                 : null,
            applyWidget = this.state.name && !this.state.successText ?
                <form onSubmit={this.handleSubmit}>
                    <input type="hidden" value={this.state.name}
                           name="tournament" />
                    <button type="submit">
                        Apply to play in {this.state.name}
                    </button>
                </form>
                : null;

        return (
            <div>
                <p>{this.state.successText}</p>
                <p>{this.state.error}</p>
                {infoWidget}
                {applyWidget}
            </div>
        );
    }
});

ReactDOM.render(
    <TournamentInfoPage />,
    document.getElementById("content")
);
