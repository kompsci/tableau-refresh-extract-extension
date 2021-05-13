(function () {
  $(document).ready(function () {

    //let urlPrefix = window.urlPrefix;

    //add button click event handler
    $('#actionButton').click(runAction);

    tableau.extensions.initializeAsync().then(function () {
      console.log('Initialized Dashboard API');


    });
  }, function (err) {
    // Something went wrong in initialization.
    console.error('Error while Initializing: ', err);
  });
}());


async function runAction() {
  console.log('running action...')
    let buttonName = $('#actionButton').text();

  // Show spinner
  $('#actionButton').prop('disabled', true);
  $('#actionButton').html(
    '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...'
  );

  // First identify dashboard object
  const { dashboard } = tableau.extensions.dashboardContent;
  const dashboardName = dashboard.name; // get dashboard name
  console.log(`Dashboard: ${dashboardName}`);

  // get parameters
  let queryText = "";
  parameters = await fetchParameters(dashboard);
  for(let parameter of parameters) {
    if (parameter.parameterName === 'Query') {
      queryText = parameter.parameterValue
    }
  }
  console.log(`Query Text: ${queryText}`)
  // send query text
   socket.emit('run-action', {data: queryText});


  $('#actionButton').prop('disabled', false);
  $('#actionButton').text(buttonName);

}

async function fetchParameters(dashboard) {
  console.log(`Fetching Parameters for ${dashboard.name}`);

  const parameters = [];

  const params = await dashboard.getParametersAsync();

  params.forEach((p) => {
    const parameterName = p.name;
    const parameterType = p.dataType;
    const parameterValue = p.currentValue.formattedValue;
    parameters.push({ parameterName, parameterType, parameterValue });
  });

  return parameters;
}

