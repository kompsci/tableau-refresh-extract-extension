let buttonName = 'Run Action';

(function () {
  $(document).ready(function () {

    //let urlPrefix = window.urlPrefix;
    let buttonName = $('#actionButton').text();

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

function postQuery(queryText) {

  // post query text
  const urlPrefix = window.location.href.replace(/\/+$/, '');
  const url = `${urlPrefix}/runAction`;
  payload = { "query": queryText };
  // post data
  fetch('runAction', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: {
      'Content-type': 'application/json; charset=utf-8',
    }
  })
    .then((res) => {
      if (res.status == 200) {

        console.log('Run action successful...')
      }
    })
    .catch((error) => {
      console.error('Error: ', error);
      $('#actionButton').prop('disabled', false);
      $('#actionButton').text(buttonName);
    });
}

async function runAction() {
  console.log('running action...')

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
    if (parameter.parameterName === 'query') {
      queryText = parameter.parameterValue
    }
  }
  console.log(`Query Text: ${queryText}`)
  postQuery(queryText);


}

async function afterAction() {
  const { dashboard } = tableau.extensions.dashboardContent;

  log('Refreshing Dashboard...');
  await refreshData(dashboard);
  log('All Done!');

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

async function refreshData(dashboard) {
  // await dashboard.worksheets.find(w => w.name === "Map")
  //   //     .getDataSourcesAsync()
  //   //     .then(datasources =>  {
  //   //       dataSource = datasources.find(datasource => datasource.name === "GooglePlacesData");
  //   //       return dataSource.refreshAsync();
  //   //       }
  //   //     );

  await dashboard.worksheets.find(w => w.name === "Data")
      .getDataSourcesAsync()
      .then(datasources =>  {
        dataSource = datasources.find(datasource => datasource.name === "GooglePlacesData");
        return dataSource.refreshAsync();
        }
      );
}

